# Review instructions

<!-- 初始化後依專案調整 <...> 佔位內容；只放 review 專用規則，保持精簡 -->

只放 PR review 專用規則；專案慣例以 `CLAUDE.md` 為準，這裡不重複。review 留言用繁體中文，程式碼與識別名稱保留英文。
本檔同時供本機 `/review`（code-reviewer subagent）與 GitHub 上的 Claude review 使用。

## What Important means here

本專案品質順序是 <例如 正確性 > 安全性 > 穩定性 > 效能>。Important 只用在會造成錯誤結果、資料錯誤或遺失、程序崩潰、安全問題，或未經同意寫入外部系統的情況：

- 邏輯錯誤、邊界條件處理錯誤，會產生錯誤結果
- 資料被覆蓋或遺失；例外被靜默吞掉、錯誤沒有記錄
- 資源沒有釋放、競態條件；queue 或 buffer 沒有上限
- 注入（SQL / 指令）、權限檢查缺漏
- 機密寫死在程式碼或寫進 log
- 不安全的 migration（會遺失資料、修改既有 migration）
- 違反 `CLAUDE.md` 的分層規則，或未先詢問就呼叫會寫入外部系統的函式
- 用了查不到文件、未經驗證的第三方 API
- <專案特有、一定要擋下的錯誤類型>

命名、風格、重構建議最多是 Nit。

## Cap the nits

每次 review 最多 5 個 Nit。

## Do not report

- 格式與 import 排序（formatter / linter 處理）
- lockfile
- `review-scope` 中標為 `exclude` 的檔案
- <第三方或不可修改的目錄，例如 `vendor/`>

## Review coverage

每個變更檔案都要審完，沒有「預算不夠可跳過」的例外。要審哪些檔案、分給哪個分片，由 `.github/scripts/review_plan.py` 依下方 `review-scope` 區塊決定；分到的檔案必須全部審完，審不完就如實回報 partial，覆蓋閘門會讓 check 失敗。

各層級的審查深度：

1. 核心程式（例如 `src/`）：逐行審
2. 其他程式與設定，包含 `.github/`、根目錄程式：逐行審
3. `tests/`：只看是否涵蓋這次改動的行為，不審測試寫法；看完即算審完
4. `docs/`、`*.md`：只檢查下方「Always check」要求的文件同步；檢查完即算審完

`review-scope` 規則：每行 `<層級或 exclude>: <pattern>`，pattern 用 Python `fnmatch` 語法（`*` 可跨目錄），由上往下第一個符合的生效，最後一定要有 `2: *` 兜底。`exclude` 的檔案和二進位檔在 summary 記為「依規則排除」，不算未審。

```review-scope
exclude: vendor/*
exclude: uv.lock
exclude: poetry.lock
exclude: package-lock.json
exclude: pnpm-lock.yaml
exclude: yarn.lock
1: src/*
3: tests/*
4: docs/*
4: *.md
2: *
```

## Always check

- 新邏輯有對應測試，測試真的驗證行為，而且不依賴外部服務或實機
- 改了欄位、規格、測試流程或架構時，有依 `docs/guides/ai-coding-guidelines.md` §6 同步更新對應文件
- 沒有用 `print` 取代 logging；沒有新增未說明的依賴
- 沒有把機密、產生的資料或大型二進位檔加進 git
