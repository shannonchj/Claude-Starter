#!/usr/bin/env python3
"""claude-starter 初始化腳本：將 core/ 與指定技術棧組合後複製到目標專案。

用法：
    python3 init.py --list
    python3 init.py <target-dir> [--force]            # 使用預設技術棧
    python3 init.py <stack> <target-dir> [--force]
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORE = ROOT / "core"
STACKS = ROOT / "stacks"
MARKER = "<!-- @@STACK@@ -->"
# 與 core/.github/scripts/review_plan.py 的 SCOPE_BLOCK 相同
SCOPE_BLOCK = re.compile(r"^```review-scope[ \t]*\r?\n(.*?)^```", re.MULTILINE | re.DOTALL)
DEFAULT_STACK = "python-fastapi"
# Windows 通常沒有 python3 指令，產生 settings.json 時改用 python
PYTHON_CMD = "python" if sys.platform == "win32" else "python3"


def available_stacks():
    return sorted(p.name for p in STACKS.iterdir() if p.is_dir() and not p.name.startswith("_"))


def copy_tree(src: Path, dst: Path, force: bool, skip=()):
    copied, skipped = [], []
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if path.is_dir() or rel.as_posix() in skip or path.name == ".gitkeep":
            continue
        target = dst / rel
        if target.exists() and not force:
            skipped.append(rel.as_posix())
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(rel.as_posix())
    return copied, skipped


def merge_settings(base: dict, extra: dict) -> dict:
    result = json.loads(json.dumps(base))
    for key, value in extra.items():
        if key == "permissions":
            perms = result.setdefault("permissions", {})
            for kind, rules in value.items():
                if isinstance(rules, list):
                    current = perms.setdefault(kind, [])
                    current.extend(r for r in rules if r not in current)
                else:
                    perms[kind] = rules
        elif key == "hooks":
            hooks = result.setdefault("hooks", {})
            for event, entries in value.items():
                hooks.setdefault(event, []).extend(entries)
        elif key.startswith("_"):
            continue
        else:
            result[key] = value
    return result


def split_sections(text: str):
    """切成 [(標題行, 內容行)]，只認 `## ` 二級標題；第一個標題之前的內容丟棄。"""
    sections, heading, body = [], None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if heading is not None:
                sections.append((heading, body))
            heading, body = line.strip(), []
        elif heading is not None:
            body.append(line)
    if heading is not None:
        sections.append((heading, body))
    return sections


def merge_claude_md(base: str, stack: str) -> str:
    """stack 中與 base 同名的 `##` 段落取代 base 內容，其餘段落插入 MARKER 位置。"""
    lines = base.splitlines()
    extra = []
    for heading, body in split_sections(stack):
        body = "\n".join(body).strip("\n").splitlines()
        if heading not in lines:
            extra += [heading, *body, ""]
            continue
        start = lines.index(heading) + 1
        end = start
        while end < len(lines) and not lines[end].startswith("## ") and lines[end] != MARKER:
            end += 1
        lines[start:end] = [*body, ""]
    if MARKER in lines:
        i = lines.index(MARKER)
        lines[i : i + 1] = extra
    elif extra:
        lines += ["", *extra]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).rstrip() + "\n"


def inject_review_scope(review_md: str, scope_file: Path) -> str:
    """用 stack 的 review-scope.txt（去掉註解與空行）取代 REVIEW.md 的 review-scope 區塊內容。"""
    if not scope_file.exists() or not SCOPE_BLOCK.search(review_md):
        return review_md
    rules = [
        line.strip()
        for line in scope_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not rules:
        return review_md
    block = "```review-scope\n" + "\n".join(rules) + "\n```"
    return SCOPE_BLOCK.sub(lambda _: block, review_md, count=1)


def merge_gitignore(target: Path, sources):
    """把各來源檔中目標專案還沒有的規則，連同所屬註解一起追加到 .gitignore。"""
    gitignore = target / ".gitignore"
    lines = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    added = 0
    for src in sources:
        if not src.exists():
            continue
        block, pending_comments = [], []
        for line in src.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                pending_comments = []
            elif line.startswith("#"):
                pending_comments.append(line)
            elif line not in lines and line not in block:
                comments = [c for c in pending_comments if c not in block]
                if comments and block:
                    block.append("")
                block.extend(comments)
                pending_comments = []
                block.append(line)
                added += 1
        if block:
            if lines and lines[-1].strip():
                lines.append("")
            lines.extend(block)
    if added:
        gitignore.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  更新：.gitignore（新增 {added} 條規則）")


def write_if_allowed(path: Path, content: str, force: bool, label: str):
    if path.exists() and not force:
        print(f"  略過（已存在）：{label}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  產生：{label}")


def main():
    parser = argparse.ArgumentParser(description="claude-starter 初始化")
    parser.add_argument(
        "args", nargs="*", metavar="[stack] target",
        help=f"技術棧名稱（stacks/ 下的資料夾，省略時為 {DEFAULT_STACK}）與目標專案路徑",
    )
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的檔案")
    parser.add_argument("--list", action="store_true", help="列出可用技術棧")
    args = parser.parse_args()

    if args.list:
        print("可用技術棧：")
        for name in available_stacks():
            print(f"  - {name}{'（預設）' if name == DEFAULT_STACK else ''}")
        return

    if len(args.args) == 1:
        args.stack, args.target = DEFAULT_STACK, args.args[0]
    elif len(args.args) == 2:
        args.stack, args.target = args.args
    else:
        parser.print_help()
        sys.exit(1)

    stack_dir = STACKS / args.stack
    if not stack_dir.is_dir() or args.stack.startswith("_"):
        print(f"找不到技術棧：{args.stack}。可用：{', '.join(available_stacks())}")
        sys.exit(1)

    target = Path(args.target).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    print(f"套用 core + {args.stack} → {target}")

    # 1. 複製 core（CLAUDE.base.md、REVIEW.md、settings.json、.gitignore 另外處理）
    copied, skipped = copy_tree(
        CORE,
        target,
        args.force,
        skip={"CLAUDE.base.md", "REVIEW.md", ".claude/settings.json", ".gitignore"},
    )
    for f in copied:
        print(f"  複製：{f}")
    for f in skipped:
        print(f"  略過（已存在）：{f}")

    # 2. 組合 CLAUDE.md：stack 的同名段落取代 base 佔位，其餘插入 @@STACK@@
    base = (CORE / "CLAUDE.base.md").read_text(encoding="utf-8")
    stack_md_path = stack_dir / "CLAUDE.stack.md"
    stack_md = stack_md_path.read_text(encoding="utf-8") if stack_md_path.exists() else ""
    write_if_allowed(target / "CLAUDE.md", merge_claude_md(base, stack_md), args.force, "CLAUDE.md")

    # 2b. REVIEW.md：注入 stack 的 review-scope
    review_md = inject_review_scope(
        (CORE / "REVIEW.md").read_text(encoding="utf-8"), stack_dir / "review-scope.txt"
    )
    write_if_allowed(target / "REVIEW.md", review_md, args.force, "REVIEW.md")

    # 3. 合併 settings.json
    settings = json.loads((CORE / ".claude" / "settings.json").read_text(encoding="utf-8"))
    stack_settings_path = stack_dir / "settings.stack.json"
    if stack_settings_path.exists():
        settings = merge_settings(
            settings, json.loads(stack_settings_path.read_text(encoding="utf-8"))
        )
    settings_text = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"
    settings_text = settings_text.replace('"python3 ', f'"{PYTHON_CMD} ')
    write_if_allowed(
        target / ".claude" / "settings.json",
        settings_text,
        args.force,
        ".claude/settings.json",
    )

    # 4. 複製 stack 的 hooks / skills / agents
    for sub in ("hooks", "skills", "agents"):
        src = stack_dir / sub
        if src.is_dir():
            c, s = copy_tree(src, target / ".claude" / sub, args.force)
            for f in c:
                print(f"  複製：.claude/{sub}/{f}")
            for f in s:
                print(f"  略過（已存在）：.claude/{sub}/{f}")

    # hooks 設為可執行
    hooks_dir = target / ".claude" / "hooks"
    if hooks_dir.is_dir():
        for h in hooks_dir.glob("*.py"):
            h.chmod(h.stat().st_mode | 0o111)

    # 5. .gitignore：合併 core 與 stack 的規則，只追加目標專案缺少的行
    merge_gitignore(target, [CORE / ".gitignore", stack_dir / "gitignore"])

    print("\n完成。接下來：")
    print("  1. 編輯 CLAUDE.md、REVIEW.md、docs/guides/ai-coding-guidelines.md，替換 <...> 佔位內容")
    print("  2. 確認 REVIEW.md 的 review-scope 符合專案目錄")
    print("  3. 在專案中啟動 claude，執行 /init 補充並人工審核")
    print("  4. 執行 /hooks 確認 hooks 已載入")
    print("  5. GitHub PR review：repo secrets 設定 CLAUDE_CODE_OAUTH_TOKEN；要擋合併就把 summary 設為 required check")


if __name__ == "__main__":
    main()
