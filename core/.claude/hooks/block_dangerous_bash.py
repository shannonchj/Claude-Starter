#!/usr/bin/env python3
"""PreToolUse hook (Bash)：攔截危險指令。exit 2 = 阻擋，stderr 內容會回饋給 Claude。"""
import json
import re
import sys

RULES = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+(/|~|\$HOME)(\s|$)", "禁止刪除根目錄或家目錄"),
    (r"\bgit\s+push\b.*\s(origin\s+)?(main|master)(\s|$)", "禁止直接 push 到 main/master，請推送分支並開 PR"),
    (r"\bgit\s+push\b.*(--force\b|\s-f\b)", "禁止 force push；如確有需要請由使用者手動執行"),
    (r"\bgit\s+reset\s+--hard\b", "禁止 git reset --hard，可能遺失未提交的變更"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "禁止 git clean -f，可能刪除未追蹤檔案"),
    (r"\b(DROP\s+(DATABASE|SCHEMA)|TRUNCATE\s+TABLE)\b", "禁止執行破壞性 SQL"),
    (r"\bchmod\s+(-R\s+)?777\b", "禁止 chmod 777"),
    (r"(curl|wget)[^|]*\|\s*(ba|z)?sh\b", "禁止下載後直接執行腳本"),
]


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    command = data.get("tool_input", {}).get("command", "")
    for pattern, reason in RULES:
        if re.search(pattern, command, re.IGNORECASE):
            print(f"已阻擋：{reason}\n指令：{command}", file=sys.stderr)
            sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
