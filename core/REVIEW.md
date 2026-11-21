# Review instructions

<!-- 初始化後依專案調整 TODO 項目；只放 review 專用規則，保持精簡 -->

只放 PR review 專用規則；專案慣例以 `CLAUDE.md` 為準，這裡不重複。review 留言用繁體中文，程式碼與識別名稱保留英文。
本檔同時供本機 `/review`（code-reviewer subagent）與 GitHub 上的 Claude review 使用。

## What Important means here

Important 只用在會造成錯誤結果、資料遺失、程序崩潰或安全問題的情況：

- 邏輯錯誤、邊界條件處理錯誤，會產生錯誤結果
- 資料被覆蓋或遺失；例外被靜默吞掉
- 資源沒有釋放、競態條件
- 注入（SQL / 指令）、權限檢查缺漏
- 機密寫死在程式碼或寫進 log
- 不安全的 migration（會遺失資料、修改既有 migration）
<!-- TODO：加入專案特有的 Important 條件 -->

命名、風格、重構建議最多是 Nit。

## Cap the nits

每次 review 最多 5 個 Nit。

## Do not report

- 格式與 import 排序（formatter / linter 處理）
- lockfile
<!-- TODO：加入第三方或不可修改的目錄 -->

## Always check

- 新邏輯有對應測試，且測試真的驗證行為
- 改了規格、測試流程或架構時，有同步更新 `docs/`
- 沒有用 `print` 取代 logging；沒有新增未說明的依賴
- 沒有把機密、產生的資料或大型二進位檔加進 git
