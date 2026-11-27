# 專案開發文件

<一句話說明本文件包的用途。>

## 目錄與放置規則

新文件**一律依用途放進下表的資料夾**，不放在 `docs/` 根目錄。檔名用英文 kebab-case，不加順序編號。新增或搬移文件時，要同步更新本表與「文件導覽」。

| 資料夾 | 放什麼 | 檔名規則 |
|---|---|---|
| `docs/`（根目錄） | 只放 `README.md`、`progress.md`、`progress-archive.md` | — |
| `requirements/` | 外部提供的需求來源（客戶或團隊給的規格表），內容以來源為準，不寫實作設計 | `<主題>-spec.md` |
| `specs/` | 功能規格＋實作計畫，一個可驗收的功能一份（`/plan-feature` 產出） | `YYYY-MM-DD-<slug>.md`，依 `_template.md` |
| `decisions/` | ADR：重大架構選擇與理由 | `NNNN-<slug>.md`，依 `0000-template.md` |
| `architecture/` | 系統分層、目錄、執行緒、資料流、資料契約 | 主題名 |
| `planning/` | 里程碑、路線、優先順序 | 主題名 |
| `guides/` | 開發規範、流程、回報格式、執行指令 | 主題名 |
| `testing/` | 測試計畫、品質指標、報告範本、測試結果紀錄 | 主題名 |

判斷原則：
- 「別人給的需求」放 `requirements/`；「我們決定怎麼做」放 `specs/`（功能）或 `decisions/`（架構取捨）
- 只描述一個功能的設計，放在該功能的 spec 裡；跨功能、長期有效的設計才放 `architecture/`

## 文件導覽

| 文件 | 用途 |
|---|---|
| [architecture/overview.md](architecture/overview.md) | 系統概觀、模組職責、資料模型、外部依賴 |
| [specs/](specs/) | 各功能規格與實作計畫 |
| [decisions/](decisions/) | ADR |
| [guides/ai-coding-guidelines.md](guides/ai-coding-guidelines.md) | AI 必須遵守的開發規則、文件同步對照、回報格式 |
| [progress.md](progress.md) | 目前進度（由 `/progress` 維護） |
