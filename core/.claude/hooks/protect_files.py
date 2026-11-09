#!/usr/bin/env python3
"""PreToolUse hook (Read/Edit/Write)：保護機密檔案與 lockfile。exit 2 = 阻擋。"""
import json
import sys
from pathlib import PurePath

SECRET_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json"}
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
LOCKFILES = {
    "uv.lock", "poetry.lock", "Pipfile.lock",
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "Cargo.lock", "go.sum", "composer.lock", "Gemfile.lock",
}


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    tool = data.get("tool_name", "")
    path = data.get("tool_input", {}).get("file_path", "")
    if not path:
        sys.exit(0)
    p = PurePath(path)
    name = p.name

    is_secret = (
        name in SECRET_NAMES
        or (name.startswith(".env.") and name != ".env.example")
        or p.suffix in SECRET_SUFFIXES
        or "secrets" in p.parts
    )
    if is_secret:
        print(f"已阻擋：{path} 為機密檔案，不可讀取或修改。需要設定值請詢問使用者或參考 .env.example", file=sys.stderr)
        sys.exit(2)

    if tool in {"Edit", "MultiEdit", "Write"} and name in LOCKFILES:
        print(f"已阻擋：不可手動編輯 {name}，請使用套件管理工具更新依賴（且需先詢問使用者）", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
