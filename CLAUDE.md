# CLAUDE.md

<!-- 原則：只寫 Claude 從程式碼看不出來的事；控制在 200 行內；細節用 @ 引用外部文件 -->

## 專案概述
<專案名稱>：<一句話描述用途>。後端 API，使用 Python 3.12 + FastAPI + PostgreSQL 16。

## 常用指令
- 安裝依賴：`uv sync`
- 啟動開發伺服器：`uv run fastapi dev app/main.py`
- 啟動本地 DB：`docker compose up -d db`
- 測試：`uv run pytest -x -q`（單一檔案：`uv run pytest tests/path/test_x.py -q`）
- Lint / 格式化：`uv run ruff check --fix . && uv run ruff format .`
- 型別檢查：`uv run mypy app`
- 產生 migration：`uv run alembic revision --autogenerate -m "<描述>"`
- 套用 migration：`uv run alembic upgrade head`

## 目錄結構
- `app/main.py` — FastAPI 進入點、router 註冊
- `app/api/` — 路由層（只做參數驗證與呼叫 service，不寫商業邏輯）
- `app/services/` — 商業邏輯
- `app/repositories/` — DB 存取（SQLAlchemy 查詢只能出現在這裡）
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic request/response schemas
- `app/core/` — 設定（pydantic-settings）、DB session、安全性
- `alembic/` — migrations
- `tests/` — 結構對應 `app/`

詳細架構見 @docs/architecture.md

## 程式碼慣例
- SQLAlchemy 2.0 async 寫法（`select()` + `AsyncSession`），不使用舊版 `session.query()`
- Pydantic v2（`model_config`、`model_validate`），不使用 v1 的 `Config` / `parse_obj`
- 依賴注入一律用 `Depends`，DB session 從 `app/core/db.py:get_session` 取得
- ORM model 不可直接回傳給前端，必須轉成 `schemas/` 中的 response model
- 所有函式加型別註記；錯誤用自訂例外 + `app/core/exceptions.py` 的 handler，不在 router 裡寫 try/except
- 設定值從環境變數讀取（`app/core/config.py`），不可寫死

## 資料庫規則
- 修改 model 後必須產生 migration，並人工檢查 autogenerate 結果
- 不要修改已存在的 migration 檔，只能新增
- 金額用 `Numeric`，時間一律 `TIMESTAMP WITH TIME ZONE`（UTC）

## 測試
- 新功能或修 bug 必須附測試；測試使用獨立 test DB（見 `tests/conftest.py`）
- API 測試用 `httpx.AsyncClient`；完成任務前必須確認 `pytest` 與 `ruff` 全部通過

## Git 流程
- 分支：`feat/<主題>`、`fix/<主題>`；不可直接 push 到 main
- Commit 訊息遵循 Conventional Commits（`feat: ...`、`fix: ...`）

## 禁止事項
- 不要讀取或修改 `.env`、`*.pem` 等機密檔案
- 不要新增依賴套件，除非先詢問我
- 不要加多餘註解或為了「以防萬一」新增未要求的功能
- 不確定需求時先提問，不要自行假設

## 工作方式
- 較大的改動先用 Plan mode 提出計畫，我確認後再實作
- 回覆使用繁體中文；程式碼、識別名稱用英文
