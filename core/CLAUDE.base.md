# CLAUDE.md

<!--
維護原則：
- 只寫 Claude 從程式碼看不出來的事，控制在 200 行內
- @path 引用每次 session 都會載入；非必要的文件寫成「需要時讀 docs/xxx.md」
- 規則改了就改這份檔案（進 git review），不要只在對話中口頭交代
-->

## 專案概述
<專案名稱>：<一句話描述用途與使用者>。

<!-- @@STACK@@ -->

## 文件位置（需要時再讀，不要一開始全部讀取）
- 架構說明：`docs/architecture.md`
- 進度與待辦：`docs/progress.md`
- 功能規格：`docs/specs/`
- 架構決策紀錄（ADR）：`docs/decisions/`

## Git 流程
- 分支命名：`feat/<主題>`、`fix/<主題>`、`chore/<主題>`
- 不可直接 push 到 main / master，一律透過 PR
- Commit 訊息遵循 Conventional Commits（`feat: ...`、`fix: ...`、`refactor: ...`）

## 禁止事項
- 不要讀取或修改 `.env`、金鑰、憑證等機密檔案
- 不要新增或升級依賴套件，除非先詢問我
- 不要手動編輯 lockfile
- 不要加多餘註解，不要新增未被要求的功能
- 不確定需求時先提問，不要自行假設

## 工作方式
- 較大的改動先用 Plan mode 提出計畫，我確認後再實作
- 完成任務前，必須執行本檔「常用指令」中的測試與 lint，並確認全部通過
- 長任務：開始時讀 `docs/progress.md`，告一段落時用 `/progress` 更新
- 大範圍搜尋程式碼交給 researcher subagent，只回報結論
- 回覆使用繁體中文；程式碼、識別名稱、commit 訊息使用英文
