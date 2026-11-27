#!/usr/bin/env python3
"""舊用法相容入口（不需安裝）。建議改用 `claude-starter` 指令，見 README。

用法：
    python3 init.py --list
    python3 init.py <target-dir> [--force]            # 使用預設技術棧
    python3 init.py <stack> <target-dir> [--force]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from claude_starter.cli import DEFAULT_STACK, apply, print_stacks, use_utf8_stdio  # noqa: E402


def main() -> int:
    use_utf8_stdio()
    parser = argparse.ArgumentParser(description="claude-starter 初始化（舊用法）")
    parser.add_argument(
        "args", nargs="*", metavar="[stack] target",
        help=f"技術棧名稱（stacks/ 下的資料夾，省略時為 {DEFAULT_STACK}）與目標專案路徑",
    )
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的檔案")
    parser.add_argument("--list", action="store_true", help="列出可用技術棧")
    args = parser.parse_args()

    if args.list:
        print_stacks()
        return 0
    if len(args.args) == 1:
        stack, target = DEFAULT_STACK, args.args[0]
    elif len(args.args) == 2:
        stack, target = args.args
    else:
        parser.print_help()
        return 1
    return apply(stack, target, args.force)


if __name__ == "__main__":
    sys.exit(main())
