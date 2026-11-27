"""Merge shard review results, post inline findings, write the summary and enforce coverage."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("review_summary")

SUMMARY_MARKER = "<!-- claude-review-summary -->"
NIT_CAP = 5
SEVERITY_LABEL = {
    "important": "Important",
    "nit": "Nit",
    "pre_existing": "Pre-existing",
}
SEVERITY_ORDER = ["important", "pre_existing", "nit"]


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    line: int
    body: str


@dataclass
class Merged:
    reviewed: list[str] = field(default_factory=list)
    pending: dict[str, str] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    dropped_nits: int = 0
    notes: list[str] = field(default_factory=list)
    usage: list[dict[str, object]] = field(default_factory=list)


def load_shard_result(
    shard_dir: Path,
) -> tuple[dict[str, object] | None, dict[str, object]]:
    """Return (structured output or None, usage dict) written by one matrix job."""
    structured: dict[str, object] | None = None
    raw = shard_dir / "structured.json"
    if raw.is_file() and raw.read_text(encoding="utf-8").strip():
        try:
            structured = json.loads(raw.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("%s: structured output is not valid JSON", shard_dir.name)
    usage_file = shard_dir / "usage.json"
    usage: dict[str, object] = {}
    if usage_file.is_file():
        try:
            usage = json.loads(usage_file.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            log.warning("%s: usage is not valid JSON", shard_dir.name)
    return structured, usage


def merge(
    plan: dict[str, object],
    results: dict[str, tuple[dict[str, object] | None, dict[str, object]]],
) -> Merged:
    merged = Merged()
    findings: list[Finding] = []
    for shard in plan["shards"]:
        shard_id = shard["id"]
        assigned = [f["path"] for f in shard["files"]]
        structured, usage = results.get(shard_id, (None, {}))
        merged.usage.append({"id": shard_id, "files": len(assigned), **usage})
        if structured is None:
            for path in assigned:
                merged.pending[path] = "分片失敗或沒有回傳結果"
            continue

        partial = {
            p["path"]: p["reason"]
            for p in structured.get("partial", [])
            if p.get("path") in assigned
        }
        reviewed = {
            p
            for p in structured.get("reviewed", [])
            if p in assigned and p not in partial
        }
        for path in assigned:
            if path in reviewed:
                merged.reviewed.append(path)
            elif path in partial:
                merged.pending[path] = f"只審了一部分：{partial[path]}"
            else:
                merged.pending[path] = "分片沒有回報這個檔案"
        for f in structured.get("findings", []):
            if f.get("path") in assigned and f.get("severity") in SEVERITY_LABEL:
                findings.append(
                    Finding(f["severity"], f["path"], int(f["line"]), f["body"].strip())
                )
        note = str(structured.get("notes") or "").strip()
        if note:
            merged.notes.append(note)

    findings.sort(key=lambda f: (SEVERITY_ORDER.index(f.severity), f.path, f.line))
    nits = 0
    for f in findings:
        if f.severity == "nit":
            nits += 1
            if nits > NIT_CAP:
                merged.dropped_nits += 1
                continue
        merged.findings.append(f)
    return merged


def comment_body(f: Finding) -> str:
    return f"**{SEVERITY_LABEL[f.severity]}**：{f.body}"


def usage_line(u: dict[str, object]) -> str:
    head = f"- {u['id']}：{u['files']} 檔，"
    if u.get("turns") is None and u.get("cost_usd") is None:
        return head + "沒有用量資料"
    turns = u.get("turns", "?")
    cost = (
        f"${float(u['cost_usd']):.3f}" if u.get("cost_usd") is not None else "花費不明"
    )
    subtype = f"（{u['subtype']}）" if u.get("subtype") not in (None, "success") else ""
    return f"{head}{turns} turns，{cost}{subtype}"


def first_line(text: str) -> str:
    return text.strip().splitlines()[0] if text.strip() else ""


def render_summary(
    plan: dict[str, object],
    merged: Merged,
    unposted: list[Finding],
    round_no: int,
    trigger: str,
    max_auto_rounds: int,
    label: str,
    head_sha: str,
) -> str:
    counts = {
        s: sum(1 for f in merged.findings if f.severity == s) for s in SEVERITY_LABEL
    }
    lines = [
        SUMMARY_MARKER,
        f"## Claude review 第 {round_no} 輪",
        "",
        f"Important：{counts['important']}／Nit：{counts['nit']}／Pre-existing：{counts['pre_existing']}",
        "",
    ]
    if merged.findings:
        lines += [
            f"- {SEVERITY_LABEL[f.severity]}：`{f.path}:{f.line}` {first_line(f.body)}"
            for f in merged.findings
        ]
    else:
        lines.append("本輪沒有發現問題。")
    if merged.dropped_nits:
        lines.append(
            f"- 另有 {merged.dropped_nits} 個 Nit 超過每輪上限 {NIT_CAP} 個，未列出"
        )
    if unposted:
        lines += ["", "以下問題無法留在對應行（行號不在 diff 範圍內），完整內容："]
        lines += [f"- `{f.path}:{f.line}` {comment_body(f)}" for f in unposted]
    if merged.notes:
        lines += ["", "觀察："] + [f"- {n}" for n in merged.notes]

    mode = (
        "增量（自上一輪之後的變更與先前未審檔案）"
        if plan["mode"] == "incremental"
        else "完整"
    )
    lines += [
        "",
        f"範圍：{mode}",
        f"覆蓋：{len(merged.reviewed)} / {plan['count']} 個檔案",
    ]
    excluded = plan["excluded"]
    if excluded:
        lines.append(
            f"依規則排除：{len(excluded)} 個（"
            + "、".join(f"`{e['path']}`" for e in excluded)
            + "）"
        )
    if merged.pending:
        lines.append("未審：")
        lines += [f"- `{p}`：{reason}" for p, reason in merged.pending.items()]
    else:
        lines.append("未審：無")

    if merged.usage:
        lines += ["", "<details><summary>用量</summary>", ""]
        lines += [usage_line(u) for u in merged.usage]
        missing = sum(1 for u in merged.usage if u.get("cost_usd") is None)
        total = sum(
            float(u["cost_usd"]) for u in merged.usage if u.get("cost_usd") is not None
        )
        lines.append(
            f"- 合計：${total:.3f}"
            + (f"（{missing} 個分片沒有用量資料，未計入）" if missing else "")
        )
        lines += ["", "</details>"]

    if trigger == "auto" and round_no == max_auto_rounds:
        limit_note = (
            f"已達自動 review 上限（{max_auto_rounds} 輪），之後的 push 不會自動 review。"
            f"請人工判斷剩餘問題；需要再跑一輪時，移除後重新加上 label {label}。"
        )
        lines += ["", limit_note]
    state = {"reviewed_sha": head_sha, "pending": list(merged.pending)}
    lines += [
        "",
        f"<!-- claude-review-state: {json.dumps(state, ensure_ascii=False)} -->",
    ]
    return "\n".join(lines) + "\n"


def gh_post_inline(repo: str, pr: int, head_sha: str) -> Callable[[Finding], bool]:
    def post(f: Finding) -> bool:
        result = subprocess.run(
            [
                "gh", "api", "--method", "POST", f"repos/{repo}/pulls/{pr}/comments",
                "-f", f"body={comment_body(f)}",
                "-f", f"commit_id={head_sha}",
                "-f", f"path={f.path}",
                "-F", f"line={f.line}",
                "-f", "side=RIGHT",
            ],
            capture_output=True,
            text=True,
            check=False,
        )  # fmt: skip
        if result.returncode != 0:
            log.warning(
                "inline comment on %s:%d failed: %s",
                f.path,
                f.line,
                result.stderr.strip(),
            )
        return result.returncode == 0

    return post


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument(
        "--results-dir",
        type=Path,
        required=True,
        help="contains one sub-directory per shard id",
    )
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--trigger", choices=["auto", "manual"], required=True)
    parser.add_argument("--max-auto-rounds", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument(
        "--out", type=Path, required=True, help="where to write the summary markdown"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="do not post inline comments"
    )
    args = parser.parse_args(argv)

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    results = {
        s["id"]: load_shard_result(args.results_dir / s["id"]) for s in plan["shards"]
    }
    merged = merge(plan, results)

    post = (
        (lambda f: False)
        if args.dry_run
        else gh_post_inline(args.repo, args.pr, args.head_sha)
    )
    unposted = [f for f in merged.findings if not post(f)]

    args.out.write_text(
        render_summary(
            plan,
            merged,
            unposted,
            args.round,
            args.trigger,
            args.max_auto_rounds,
            args.label,
            args.head_sha,
        ),
        encoding="utf-8",
    )
    if merged.pending:
        log.error(
            "coverage gate failed: %d of %d files not fully reviewed",
            len(merged.pending),
            plan["count"],
        )
        return 1
    log.info("coverage gate passed: %d files reviewed", len(merged.reviewed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
