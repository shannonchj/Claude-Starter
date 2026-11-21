---
name: review
description: 審查目前尚未合併的程式碼變更（staged、unstaged 或與 main 的差異）。當使用者要 review、檢查改動、或準備 commit 前使用。
argument-hint: "[base 分支，預設 main]"
---

# 程式碼審查

1. 確認審查範圍：
   - 有未提交的變更時，審查 `git diff HEAD`
   - 否則審查 `git diff ${ARGUMENTS:-main}...HEAD`
   - 先用 `git diff --stat` 看改了哪些檔案；diff 很大時依目錄分批（例如 `src/`、`tests/`），每批各交給一個 code-reviewer，不要讓單一 reviewer 讀不完
2. 把 diff 範圍交給 **code-reviewer** subagent 審查，主對話不要自己逐行讀完整個 diff。嚴重度、Nit 上限與排除項目依根目錄 `REVIEW.md`（與 GitHub 上的 Claude review 共用）。
3. 主對話逐項核對 reviewer 回報的問題：對照實際程式碼與相關 `docs/`，推翻不了的才列入結果；被推翻的列在「已排除」並寫一句理由。
4. 執行 CLAUDE.md「常用指令」中的 lint 與測試，記錄結果。
5. 依下列格式回報，沒有項目的區塊就省略：

```
## 審查結果：<通過 / 需修正>
範圍：<diff 範圍、檔案數；沒審到的檔案要列出>
### 🔴 Important
- `檔案:行號` 問題；會出錯的情境 → 建議修法
### 🟡 Nit
- ...
### ⚪ Pre-existing
- ...
### 已排除
- `檔案:行號` reviewer 回報的內容 → 排除理由
### 測試 / Lint
- 測試：通過 / 失敗（摘要）
- Lint：通過 / 失敗（摘要）
```

6. 詢問使用者要不要直接修正 🔴 項目。**沒有得到同意前不要修改檔案。**
