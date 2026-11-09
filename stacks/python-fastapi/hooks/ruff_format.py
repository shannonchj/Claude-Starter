#!/usr/bin/env python3
"""PostToolUse hook (Edit/Write)：Claude 編輯 .py 檔後自動執行 ruff format 與 ruff check --fix。

格式化交給工具處理，就不需要在 CLAUDE.md 寫格式規則，也能節省 token。
找不到 uv 或 ruff 時直接略過，不會中斷 Claude 的工作。
"""
import json
import shutil
import subprocess
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    path = data.get("tool_input", {}).get("file_path", "")
    if not path.endswith(".py"):
        sys.exit(0)

    if shutil.which("uv"):
        base = ["uv", "run", "--quiet", "ruff"]
    elif shutil.which("ruff"):
        base = ["ruff"]
    else:
        sys.exit(0)

    for args in (["format", path], ["check", "--fix", "--quiet", path]):
        try:
            subprocess.run(base + args, capture_output=True, timeout=30)
        except (subprocess.TimeoutExpired, OSError):
            pass
    sys.exit(0)


if __name__ == "__main__":
    main()
