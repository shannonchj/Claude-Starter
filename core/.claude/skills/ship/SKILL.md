---
name: ship
description: 檢查、commit、推送分支並建立 Pull Request。只在使用者明確輸入 /ship 時執行。
disable-model-invocation: true
argument-hint: "[PR 標題或補充說明]"
---

# 交付變更

任何一步失敗就停下來回報，不要跳過。

1. **分支檢查**：執行 `git branch --show-current`。
   - 如果在 main / master：依變更內容建立 `feat/<slug>` 或 `fix/<slug>` 分支並切換過去。
2. **品質檢查**：依序執行 CLAUDE.md「常用指令」中的格式化、lint、型別檢查、測試。
   - 有失敗時先修正，修完重跑，全部通過才繼續。
3. **確認變更**：用 `git status` 和 `git diff --stat` 檢查。
   - 列出這次要 commit 的檔案，排除不相關的檔案和暫存檔。
4. **Commit**：依 Conventional Commits 撰寫英文訊息。
   - 標題 72 字元內。
   - 內文說明「為什麼」改。
   - 變更包含多個獨立主題時，拆成多個 commit。
5. **推送**：`git push -u origin <branch>`。
6. **建立 PR**：如果有 `gh` CLI，執行 `gh pr create`，PR 描述包含：
   - 摘要
   - 變更項目
   - 測試方式
   - 相關規格（`docs/specs/...`）

   補充說明：$ARGUMENTS
7. 回報 PR 連結；如果沒有 `gh`，提供 PR 標題與描述讓使用者貼上。
