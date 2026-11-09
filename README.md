# claude-starter

Claude Code 協作開發的基礎模板。分成「通用核心（core）」與「技術棧（stacks）」兩層，
用 `init.py` 組合後複製到任何新專案。

## 目錄結構

```text
claude-starter/
├── README.md
├── init.py                       # 初始化腳本：core + 指定 stack → 目標專案
├── core/                         # 通用，所有專案共用
│   ├── CLAUDE.base.md            # CLAUDE.md 骨架（技術棧段落插入 @@STACK@@ 位置）
│   ├── CLAUDE.local.md.example   # 個人專案規則範例（不進 git）
│   ├── .mcp.json                 # MCP 伺服器設定（預設空）
│   ├── .claude/
│   │   ├── settings.json         # 通用權限 + 安全 hooks
│   │   ├── hooks/
│   │   │   ├── block_dangerous_bash.py   # 擋 rm -rf、push main、force push…
│   │   │   └── protect_files.py          # 擋讀寫 .env / 金鑰、擋手改 lockfile
│   │   ├── skills/
│   │   │   ├── plan-feature/SKILL.md     # /plan-feature 需求 → 規格 → 計畫
│   │   │   ├── review/SKILL.md           # /review 交給 code-reviewer 審查 diff
│   │   │   ├── ship/SKILL.md             # /ship 檢查 → commit → push → PR
│   │   │   └── progress/SKILL.md         # /progress 更新進度檔（跨 session 記憶）
│   │   └── agents/
│   │       ├── code-reviewer.md          # 唯讀審查
│   │       ├── researcher.md             # 唯讀搜尋，只回報結論
│   │       └── test-writer.md            # 撰寫測試
│   └── docs/
│       ├── architecture.md
│       ├── progress.md
│       ├── specs/_template.md
│       └── decisions/0000-template.md
├── stacks/
│   ├── _template/                # 新增技術棧時複製這個資料夾
│   │   ├── CLAUDE.stack.md
│   │   ├── settings.stack.json
│   │   └── hooks/
│   └── python-fastapi/           # Python 3.12 + FastAPI + PostgreSQL
│       ├── CLAUDE.stack.md
│       ├── settings.stack.json
│       └── hooks/ruff_format.py
└── user/
    └── CLAUDE.md                 # 個人全域偏好 → 手動放到 ~/.claude/CLAUDE.md
```

## 快速開始

需求：Python 3.8+（init.py 與 hooks 都用 Python 撰寫，無第三方套件）。

```bash
# 列出可用技術棧
python3 init.py --list

# 套用到新專案（已存在的檔案不會被覆蓋）
python3 init.py python-fastapi ../my-project

# 強制覆蓋既有檔案
python3 init.py python-fastapi ../my-project --force
```

`init.py` 會做這些事：

1. 複製 `core/` 全部內容到目標專案
2. 把 `stacks/<stack>/CLAUDE.stack.md` 插入 `CLAUDE.base.md` 的 `@@STACK@@` 位置，產生 `CLAUDE.md`
3. 合併 `core/.claude/settings.json` 與 `stacks/<stack>/settings.stack.json`（權限清單去重、hooks 依事件合併）
4. 複製 stack 的 `hooks/`、`skills/`、`agents/`（若有）到 `.claude/`
5. 在 `.gitignore` 加入 `CLAUDE.local.md`、`.claude/settings.local.json`

## 初始化後的檢查清單

- [ ] 編輯 `CLAUDE.md`：替換所有 `<...>` 佔位內容，刪掉不適用的規則
- [ ] 在專案中啟動 Claude Code，執行 `/init` 讓它依實際程式碼補充或修正 CLAUDE.md（記得再人工審核）
- [ ] 填寫 `docs/architecture.md`
- [ ] 視需要在 `.mcp.json` 加入 MCP 伺服器（GitHub、PostgreSQL…）
- [ ] 第一次使用時執行 `/hooks` 確認 hooks 已載入
- [ ] `user/CLAUDE.md` 複製到 `~/.claude/CLAUDE.md`（只需做一次）

## 日常流程

| 階段 | 做法 |
|---|---|
| 規劃 | `/plan-feature <需求描述>` → 產出 `docs/specs/<slug>.md` → 你確認 |
| 實作 | 依計畫逐步實作；大改動先開 Plan mode（Shift+Tab） |
| 測試 | 請 test-writer agent 補測試，或在計畫中採 TDD |
| 審查 | `/review` |
| 交付 | `/ship` |
| 記錄 | 任務告一段落時 `/progress`；新 session 開頭請 Claude 讀 `docs/progress.md` |

## 新增技術棧

1. `cp -r stacks/_template stacks/<new-stack>`
2. 填寫 `CLAUDE.stack.md`（指令、目錄結構、慣例、DB 規則、測試）
3. 在 `settings.stack.json` 加入該技術棧的 `permissions.allow` 與 hooks
4. 在 `hooks/` 放格式化等腳本（參考 `python-fastapi/hooks/ruff_format.py`）
5. 需要時加入 `skills/`、`agents/` 子資料夾，init.py 會自動複製

## 節省 token 的原則（維護模板時請遵守）

- CLAUDE.md 控制在 200 行內，只寫 Claude 從程式碼看不出來的事
- `@path` 引用會在**每次** session 載入；只有每次都需要的檔案才用 `@`，其餘寫成「需要時讀 docs/xxx.md」
- 流程性的說明放 skills（呼叫時才載入），不要塞進 CLAUDE.md
- linter / formatter 會處理的事不要寫成規則，交給 hooks
- 用 `/context` 檢查 memory files 佔比，超過 5–10% 就拆分
