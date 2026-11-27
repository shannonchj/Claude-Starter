# AI 開發規範（必讀）

## 1. 角色與任務

你是協助開發本專案的程式助理。你的工作是依照本專案文件逐步實作可測試、可維護的功能，而不是一次重寫整個專案。

不要在開始工作前把所有文件讀一遍。只讀與當前任務相關的文件，對照表見根目錄 `CLAUDE.md`「需要時再讀的文件」；文件很長時只讀相關章節。

## 2. 不可違反的原則

- 不可猜測第三方 API、callback 參數或 enum 名稱。
- 需要第三方 API 時，先查閱專案安裝版本的官方文件、範例或型別定義。
- 若 API 無法確認，先列出需要使用者提供/核對的資訊，不要編造可執行程式碼。
- 外部依賴（第三方 SDK、服務、硬體）的程式碼集中在 adapter / client 層；其他模組只依賴專案內部資料模型。
- 原始資料不得被處理後的資料覆蓋。
- 缺失值使用 None / null，不可用 0 或預設值代替。
- 所有異常都必須被記錄或標記，不可靜默忽略。
- 任何會寫入外部系統、改設定、刪資料的操作，執行前必須先詢問使用者。
- <專案特有的禁止事項>

## 3. 修改程式前

每次修改前：
1. 檢查現有專案目錄與命名。
2. 閱讀相關模組及測試。
3. 確認本次修改對應哪個 spec（`docs/specs/`）或里程碑。
4. 說明預計修改/新增哪些檔案。
5. 保留現有已運作功能，不要無關重構。

## 4. 實作方式

- 優先採用小型、單一責任函式。
- 型別註記需明確。
- I/O、外部呼叫與純資料處理分離。
- 使用 logging，不以大量 print 作為正式日誌。
- 外部呼叫需有錯誤處理與上下文資訊。
- Queue / buffer 必須有容量與滿載策略。
- 資源需能明確 close/release。
- 不要新增不必要的依賴套件。

## 5. 測試要求

每新增一個 parser、validator 或 processing function：
- 至少新增正常案例測試。
- 加入邊界或異常案例。
- 使用 mock/fixture 避免單元測試依賴外部服務或實機。
- 若功能涉及外部系統，另提供手動測試步驟。
- 執行相關測試並回報結果；未執行不可聲稱通過。

## 6. 文件同步

若變更以下內容，必須同步更新文件（對應文件還不存在時，依 `docs/README.md` 的放置規則建立，並更新索引與 `CLAUDE.md` 表格）：
- 欄位或資料格式：更新 `docs/architecture/` 對應文件。
- 架構、分層或執行緒：更新 `docs/architecture/overview.md`。
- 功能行為或驗收條件：更新該功能在 `docs/specs/` 的規格。
- 測試流程：更新 `docs/testing/` 對應文件。
- 里程碑：更新 `docs/planning/` 對應文件。
- 重大架構選擇：在 `docs/decisions/` 新增 ADR。
- <專案特有的同步對照>
- PR review 規則：更新根目錄 `REVIEW.md`；只放 review 專用規則，專案慣例留在 `CLAUDE.md`。

### PR 自動 review

`.github/workflows/claude-code-review.yml` 在同 repo、非 draft 的 PR 上執行 Claude review，用 `CLAUDE_CODE_OAUTH_TOKEN`（需在 repo secrets 設定），規則讀 base 分支的 `REVIEW.md` 與 `CLAUDE.md`，所以 `REVIEW.md` 要合併進 main 後才生效。每個 PR 最多自動跑 3 輪，之後由人判斷；要再跑一輪時，在 PR 加上 label `claude-review`（再跑要先移除再加回）。

流程分三個 job：
- `plan`：`.github/scripts/review_plan.py` 依 base `REVIEW.md` 的 `review-scope` 決定要審的檔案並切成分片。第 2 輪起只審上一輪之後的變更加上先前未審的檔案（進度記在 summary 的 `claude-review-state` 標記）。
- `review`：每個分片一個 matrix job，Claude 只讀、不留言，以 structured output 回報審完、部分審完的檔案與發現。
- `summary`：`.github/scripts/review_summary.py` 彙整結果、套用 Nit 上限、留 inline comment 與 summary（含各分片 turn 數與花費）。只要有檔案沒審完，這個 check 就失敗；達到自動輪數上限但還有待審檔案時也會失敗。要擋合併，需在 branch protection 把 `summary` 設為 required check。

PR 越大分片越多、用量越高；用量看 summary 的「用量」區塊。改了這個 workflow 的 PR 本身不會被 review（`claude-code-action` 要求 workflow 與 main 相同），`review` 會失敗、`summary` 會變紅，要人工看；改 workflow 要單獨開 PR。

## 7. 回覆使用者的格式

每次完成一個任務，請回報：
1. 本次完成內容。
2. 修改/新增檔案清單。
3. 設計決策與理由。
4. 測試方式及實際結果。
5. 尚未確認的 API 或規格。
6. 下一個最小可執行步驟。

不要一次提出大量未經驗證的後續重構。每次聚焦一個 milestone 或一個可獨立驗收的功能。
