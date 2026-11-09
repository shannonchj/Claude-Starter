#!/usr/bin/env python3
"""claude-starter 初始化腳本：將 core/ 與指定技術棧組合後複製到目標專案。

用法：
    python3 init.py --list
    python3 init.py <stack> <target-dir> [--force]
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORE = ROOT / "core"
STACKS = ROOT / "stacks"
MARKER = "<!-- @@STACK@@ -->"
GITIGNORE_LINES = ["CLAUDE.local.md", ".claude/settings.local.json"]


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


def write_if_allowed(path: Path, content: str, force: bool, label: str):
    if path.exists() and not force:
        print(f"  略過（已存在）：{label}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  產生：{label}")


def main():
    parser = argparse.ArgumentParser(description="claude-starter 初始化")
    parser.add_argument("stack", nargs="?", help="技術棧名稱（stacks/ 下的資料夾）")
    parser.add_argument("target", nargs="?", help="目標專案路徑")
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的檔案")
    parser.add_argument("--list", action="store_true", help="列出可用技術棧")
    args = parser.parse_args()

    if args.list:
        print("可用技術棧：")
        for name in available_stacks():
            print(f"  - {name}")
        return

    if not args.stack or not args.target:
        parser.print_help()
        sys.exit(1)

    stack_dir = STACKS / args.stack
    if not stack_dir.is_dir() or args.stack.startswith("_"):
        print(f"找不到技術棧：{args.stack}。可用：{', '.join(available_stacks())}")
        sys.exit(1)

    target = Path(args.target).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    print(f"套用 core + {args.stack} → {target}")

    # 1. 複製 core（CLAUDE.base.md 與 settings.json 另外處理）
    copied, skipped = copy_tree(
        CORE, target, args.force, skip={"CLAUDE.base.md", ".claude/settings.json"}
    )
    for f in copied:
        print(f"  複製：{f}")
    for f in skipped:
        print(f"  略過（已存在）：{f}")

    # 2. 組合 CLAUDE.md
    base = (CORE / "CLAUDE.base.md").read_text(encoding="utf-8")
    stack_md_path = stack_dir / "CLAUDE.stack.md"
    stack_md = stack_md_path.read_text(encoding="utf-8").strip() if stack_md_path.exists() else ""
    claude_md = base.replace(MARKER, stack_md) if MARKER in base else base + "\n\n" + stack_md
    write_if_allowed(target / "CLAUDE.md", claude_md.rstrip() + "\n", args.force, "CLAUDE.md")

    # 3. 合併 settings.json
    settings = json.loads((CORE / ".claude" / "settings.json").read_text(encoding="utf-8"))
    stack_settings_path = stack_dir / "settings.stack.json"
    if stack_settings_path.exists():
        settings = merge_settings(
            settings, json.loads(stack_settings_path.read_text(encoding="utf-8"))
        )
    write_if_allowed(
        target / ".claude" / "settings.json",
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
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

    # 5. .gitignore
    gitignore = target / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    missing = [line for line in GITIGNORE_LINES if line not in existing]
    if missing:
        with gitignore.open("a", encoding="utf-8") as f:
            if existing and existing[-1].strip():
                f.write("\n")
            f.write("# Claude Code 個人設定\n" + "\n".join(missing) + "\n")
        print(f"  更新：.gitignore（{', '.join(missing)}）")

    print("\n完成。接下來：")
    print("  1. 編輯 CLAUDE.md，替換 <...> 佔位內容")
    print("  2. 在專案中啟動 claude，執行 /init 補充並人工審核")
    print("  3. 執行 /hooks 確認 hooks 已載入")


if __name__ == "__main__":
    main()
