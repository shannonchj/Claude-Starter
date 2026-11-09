## 技術棧
Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 16 + Alembic，套件管理使用 uv。

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
- `app/main.py`：FastAPI 進入點、router 註冊
- `app/api/`：路由層（只做參數驗證與呼叫 service，不寫商業邏輯）
- `app/services/`：商業邏輯
- `app/repositories/`：DB 存取（SQLAlchemy 查詢只能出現在這裡）
- `app/models/`：SQLAlchemy ORM models
- `app/schemas/`：Pydantic request/response schemas
- `app/core/`：設定（pydantic-settings）、DB session、例外處理、安全性
- `alembic/`：migrations
- `tests/`：結構對應 `app/`

## 程式碼慣例
- SQLAlchemy 2.0 async 寫法（`select()` + `AsyncSession`），不使用 `session.query()`
- Pydantic v2（`model_config`、`model_validate`），不使用 v1 的 `Config` / `parse_obj`
- 依賴注入一律用 `Depends`；DB session 從 `app/core/db.py:get_session` 取得
- ORM model 不可直接回傳，必須轉成 `schemas/` 的 response model
- 所有函式加型別註記
- 錯誤用自訂例外 + `app/core/exceptions.py` 的 handler，不在 router 寫 try/except
- 設定值從環境變數讀取（`app/core/config.py`），不可寫死

## 資料庫規則
- 修改 model 後必須產生 migration，並人工檢查 autogenerate 結果
- 不要修改已存在的 migration 檔，只能新增
- 金額用 `Numeric`；時間一律 `TIMESTAMP WITH TIME ZONE`（UTC）

## 測試
- 新功能或修 bug 必須附測試；使用獨立 test DB（見 `tests/conftest.py`）
- API 測試使用 `httpx.AsyncClient` + `pytest-asyncio`
