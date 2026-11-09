---
name: review
description: 審查目前尚未合併的程式碼變更（staged、unstaged 或與 main 的差異）。當使用者要 review、檢查改動、或準備 commit 前使用。
argument-hint: "[base 分支，預設 main]"
---

# 程式碼審查

1. 確認審查範圍：
   - 有未提交的變更時，審查 `git diff HEAD`
   - 否則審查 `git diff ${ARGUMENTS:-main}...HEAD`
   - 先用 `git diff --stat` 看改了哪些檔案
2. 把 diff 範圍交給 **code-reviewer** subagent 審查，主對話不要自己逐行讀完整個 diff。
3. 執行 CLAUDE.md「常用指令」中的 lint 與測試，記錄結果。
4. 依下列格式回報，沒有問題的等級就省略：

```
## 審查結果：<通過 / 需修正>
### 🔴 必須修正
- `檔案:行號` 問題 → 建議修法
### 🟡 建議修正
- ...
### 🟢 小地方
- ...
### 測試 / Lint
- pytest：通過 / 失敗（摘要）
```

5. 詢問使用者要不要直接修正 🔴 項目。**沒有得到同意前不要修改檔案。**
