"""Decide which PR files the Claude review must cover and split them into shards."""

from __future__ import annotations

import argparse
import fnmatch
import json
import logging
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

log = logging.getLogger("review_plan")

SCOPE_BLOCK = re.compile(
    r"^```review-scope[ \t]*\r?\n(.*?)^```", re.MULTILINE | re.DOTALL
)
STATE_MARKER = re.compile(r"<!--\s*claude-review-state:\s*(\{.*?\})\s*-->", re.DOTALL)
DEFAULT_SCOPE = [("exclude", "vendor/*"), ("exclude", "uv.lock"), ("2", "*")]


@dataclass(frozen=True)
class ShardLimits:
    max_files: int
    max_lines: int
    turns_per_file: int


# Tiers 1-2 are read line by line; tiers 3-4 only get coverage / doc-sync checks.
DEEP = ShardLimits(max_files=6, max_lines=1500, turns_per_file=8)
LIGHT = ShardLimits(max_files=15, max_lines=4000, turns_per_file=4)
LIGHT_TIERS = {3, 4}
BASE_TURNS = 20
LINES_PER_EXTRA_TURN = 100
MAX_TURNS = 120


@dataclass(frozen=True)
class ChangedFile:
    path: str
    lines: int | None


@dataclass(frozen=True)
class ReviewFile:
    path: str
    tier: int
    lines: int


def parse_scope(review_md: str) -> list[tuple[str, str]]:
    match = SCOPE_BLOCK.search(review_md)
    if match is None:
        log.warning("REVIEW.md has no review-scope block; using default scope")
        return list(DEFAULT_SCOPE)
    rules: list[tuple[str, str]] = []
    for raw in match.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, pattern = line.partition(":")
        key, pattern = key.strip(), pattern.strip()
        if (
            not sep
            or not pattern
            or (key != "exclude" and key not in {"1", "2", "3", "4"})
        ):
            raise ValueError(f"invalid review-scope rule: {raw!r}")
        rules.append((key, pattern))
    if not rules:
        raise ValueError("review-scope block is empty")
    return rules


def classify(path: str, rules: list[tuple[str, str]]) -> str | None:
    for key, pattern in rules:
        if fnmatch.fnmatchcase(path, pattern):
            return key
    return None


def parse_numstat(raw: str) -> list[ChangedFile]:
    """Parse `git diff --numstat -z --no-renames` output; binary files get lines=None."""
    files: list[ChangedFile] = []
    for entry in raw.split("\0"):
        if not entry:
            continue
        added, deleted, path = entry.split("\t", 2)
        if added == "-" or deleted == "-":
            files.append(ChangedFile(path, None))
        else:
            files.append(ChangedFile(path, int(added) + int(deleted)))
    return files


def parse_state(summary: str) -> tuple[str | None, list[str]]:
    match = STATE_MARKER.search(summary)
    if match is None:
        return None, []
    state = json.loads(match.group(1))
    return state.get("reviewed_sha"), list(state.get("pending", []))


def changed_since(sha: str, head_sha: str) -> set[str] | None:
    result = subprocess.run(
        ["git", "diff", "--name-only", "-z", "--no-renames", sha, head_sha],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        log.warning(
            "cannot diff %s..%s, falling back to full review: %s",
            sha,
            head_sha,
            result.stderr.strip(),
        )
        return None
    return {p for p in result.stdout.split("\0") if p}


def limits_for(tier: int) -> ShardLimits:
    return LIGHT if tier in LIGHT_TIERS else DEEP


def shard(files: list[ReviewFile]) -> list[list[ReviewFile]]:
    """Pack files in tier order; deep and light tiers never share a shard."""
    shards: list[list[ReviewFile]] = []
    current: list[ReviewFile] = []
    current_lines = 0
    for f in sorted(files, key=lambda f: (f.tier, f.path)):
        limits = limits_for(f.tier)
        if current:
            other_kind = limits_for(current[0].tier) is not limits
            too_many = len(current) >= limits.max_files
            too_long = current_lines + f.lines > limits.max_lines
            if other_kind or too_many or too_long:
                shards.append(current)
                current, current_lines = [], 0
        current.append(f)
        current_lines += f.lines
    if current:
        shards.append(current)
    return shards


def max_turns(files: list[ReviewFile]) -> int:
    lines = sum(f.lines for f in files)
    per_file = limits_for(files[0].tier).turns_per_file
    turns = BASE_TURNS + per_file * len(files) + lines // LINES_PER_EXTRA_TURN
    return min(turns, MAX_TURNS)


def build_plan(
    review_md: str,
    numstat: str,
    prev_summary: str | None,
    head_sha: str | None,
    full: bool,
) -> dict[str, object]:
    rules = parse_scope(review_md)
    changed = parse_numstat(numstat)

    reviewed_sha, pending = parse_state(prev_summary) if prev_summary else (None, [])
    since: set[str] | None = None
    if not full and reviewed_sha and head_sha:
        since = changed_since(reviewed_sha, head_sha)
    mode = "incremental" if since is not None else "full"

    excluded: list[dict[str, str]] = []
    to_review: list[ReviewFile] = []
    for f in changed:
        key = classify(f.path, rules)
        if key == "exclude":
            excluded.append({"path": f.path, "reason": "review-scope exclude"})
        elif f.lines is None:
            excluded.append({"path": f.path, "reason": "binary"})
        elif key is None:
            raise ValueError(
                f"no review-scope rule matches {f.path!r}; add a catch-all rule"
            )
        elif since is None or f.path in since or f.path in pending:
            to_review.append(ReviewFile(f.path, int(key), f.lines))

    shards = shard(to_review)
    return {
        "mode": mode,
        "since_sha": reviewed_sha if mode == "incremental" else None,
        "count": len(to_review),
        "to_review": [f.path for f in to_review],
        "excluded": excluded,
        "shards": [
            {"id": f"s{i}", "max_turns": max_turns(s), "files": [asdict(f) for f in s]}
            for i, s in enumerate(shards, start=1)
        ],
    }


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--review-md", type=Path, required=True, help="base branch REVIEW.md"
    )
    parser.add_argument(
        "--numstat",
        type=Path,
        required=True,
        help="git diff --numstat -z --no-renames of the PR",
    )
    parser.add_argument(
        "--prev-summary",
        type=Path,
        help="body of the latest Claude review summary comment",
    )
    parser.add_argument(
        "--head-sha", help="PR head commit, used for incremental rounds"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="ignore previous rounds and review every file",
    )
    parser.add_argument(
        "--out", type=Path, required=True, help="where to write the plan JSON"
    )
    args = parser.parse_args(argv)

    review_md = (
        args.review_md.read_text(encoding="utf-8") if args.review_md.is_file() else ""
    )
    prev = (
        args.prev_summary.read_text(encoding="utf-8")
        if args.prev_summary and args.prev_summary.is_file()
        else None
    )
    plan = build_plan(
        review_md=review_md,
        numstat=args.numstat.read_text(encoding="utf-8"),
        prev_summary=prev,
        head_sha=args.head_sha,
        full=args.full,
    )
    args.out.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info(
        "mode=%s files=%d shards=%d excluded=%d",
        plan["mode"],
        plan["count"],
        len(plan["shards"]),
        len(plan["excluded"]),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
