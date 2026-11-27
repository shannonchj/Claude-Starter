# CLAUDE.md

維護原則：這裡只放每次都用得到的基礎資訊，控制在 100 行內；細節寫進 `docs/` 對應文件，這裡只留指標。規則改了就改這份檔案（進 git review），不要只在對話中口頭交代。

## 專案
<一到三句：要做什麼、給誰用、目前階段、執行環境。>品質重點：<例如 正確性 > 安全性 > 穩定性 > 效能>。

## 環境與指令
- <語言與版本、套件管理工具>
- 安裝：`<install command>`
- 測試：`<test command>`（單一：`<single test command>`）
- Lint：`<lint/format command>`
- 型別：`<type check command>`
- 執行：`<run command>`

## 目錄
- `<dir>/`：<用途；有禁止修改或特殊規則的目錄寫在這裡>

<!-- @@STACK@@ -->

## 需要時再讀的文件
| 要做的事 | 先讀 |
|---|---|
| 分層、資料流、模組職責、外部依賴 | `docs/architecture/overview.md` |
| 開發規範、文件同步對照、回報格式 | `docs/guides/ai-coding-guidelines.md` |
| 目前進度（長任務開始時讀） | `docs/progress.md` |
| 規格、ADR、文件索引 | `docs/specs/`、`docs/decisions/`、`docs/README.md` |
| PR review 規則（`/review` 與 GitHub review 共用） | `REVIEW.md` |
| **新增或搬移任何文件** | 先看 `docs/README.md`「目錄與放置規則」：依用途放子資料夾、kebab-case、不放 `docs/` 根目錄，並更新索引與本表 |

## 核心規則
- 任何會寫入外部系統、改設定、刪資料的操作，執行前必須先詢問我
- 不可猜測第三方 API、設定或 enum；查不到就列出待確認事項，或寫小腳本實測
- 一次只做一個可驗收的功能；改了欄位、規格、測試流程或架構，要同步更新 `docs/`
- 單元測試不可依賴外部服務或實機；沒實際跑過的測試不可回報為通過
- 不讀取、不修改 `.env`、金鑰、憑證（`.env.example` 例外：可讀寫，新增設定項時同步更新，只放佔位值）
- 未經詢問不新增或升級依賴，不手動編輯 lockfile
- 用 logging 不用 print；不加多餘註解與沒被要求的功能；需求不確定時先提問

## Git
- 分支 `feat/`、`fix/`、`chore/<主題>`；不可直接 push 到 main，一律開 PR；Conventional Commits
- 不進 git：<資料、產出物、授權不可轉讓的檔案>

## 工作方式
- 較大的改動先用 Plan mode 提出計畫，確認後再實作
- 完成前要跑「環境與指令」中的測試與 lint，全部通過才算完成；依 `docs/guides/ai-coding-guidelines.md` §7 格式回報
- 長任務開始時讀 `docs/progress.md`，告一段落用 `/progress` 更新；大範圍搜尋交給 researcher subagent
- 回覆使用繁體中文；程式碼、識別名稱、commit 訊息使用英文
