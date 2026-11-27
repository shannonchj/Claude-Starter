# claude-starter

Claude Code 協作開發的基礎模板。分成「通用核心（core）」與「技術棧（stacks）」兩層，
用 `claude-starter` 指令組合後複製到任何專案。

## 目錄結構

```text
claude-starter/
├── README.md
├── pyproject.toml                # 打包設定：註冊 claude-starter 指令，core/、stacks/ 打包為模板
├── init.py                       # 舊用法相容入口（不需安裝）
├── src/claude_starter/cli.py     # 指令本體：core + 指定 stack → 目標專案
├── core/                         # 通用，所有專案共用
│   ├── CLAUDE.base.md            # CLAUDE.md 骨架（stack 同名段落取代佔位，其餘插入 @@STACK@@）
│   ├── CLAUDE.local.md.example   # 個人專案規則範例（不進 git）
│   ├── REVIEW.md                 # PR review 規則（/review 與 GitHub review 共用，含 review-scope）
│   ├── .gitignore                # 通用忽略規則（與目標專案既有 .gitignore 合併）
│   ├── .mcp.json                 # MCP 伺服器設定（預設空）
│   ├── .github/
│   │   ├── workflows/claude-code-review.yml  # PR 自動 review：plan → 分片 review → summary
│   │   └── scripts/
│   │       ├── review_plan.py            # 依 review-scope 決定要審的檔案、切分片、增量輪次
│   │       └── review_summary.py         # 彙整結果、留 inline comment、覆蓋率閘門
│   ├── .claude/
│   │   ├── settings.json         # 通用權限 + 安全 hooks
│   │   ├── hooks/
│   │   │   ├── block_dangerous_bash.py   # 擋 rm -rf、push main、force push…
│   │   │   └── protect_files.py          # 擋讀寫 .env / 金鑰（.env.example 可讀寫）、擋手改 lockfile
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
│       ├── README.md                     # 文件放置規則與導覽
│       ├── progress.md                   # 進度（/progress 維護，40 行內）
│       ├── progress-archive.md           # 進度存檔（平常不讀）
│       ├── architecture/overview.md
│       ├── guides/ai-coding-guidelines.md  # AI 開發規範、文件同步對照、回報格式
│       ├── specs/_template.md
│       └── decisions/0000-template.md
├── stacks/
│   ├── _template/                # 新增技術棧時複製這個資料夾
│   │   ├── CLAUDE.stack.md
│   │   ├── settings.stack.json
│   │   ├── review-scope.txt      # 注入 REVIEW.md 的 review-scope
│   │   ├── gitignore             # 技術棧專屬忽略規則
│   │   └── hooks/
│   └── python-fastapi/           # Python 3.12 + FastAPI + PostgreSQL
│       ├── CLAUDE.stack.md
│       ├── settings.stack.json
│       ├── review-scope.txt
│       ├── gitignore
│       └── hooks/ruff_format.py
└── user/
    └── CLAUDE.md                 # 個人全域偏好 → 手動放到 ~/.claude/CLAUDE.md
```

## 快速開始

需求：[uv](https://docs.astral.sh/uv/)、Python 3.8+（指令與 hooks 都用 Python 撰寫，無第三方套件）；GitHub Actions 上的 review 腳本使用 Python 3.10。

### 安裝成指令（建議）

```bash
# 安裝一次（只寫入使用者目錄：uv 的 tools 資料夾與 ~/.local/bin，不影響系統 Python）
uv tool install git+https://github.com/shannonchj/Claude-Starter

# 在專案資料夾中執行
cd my-project
claude-starter                          # 預設技術棧 python-fastapi，已存在的檔案不會被覆蓋
claude-starter --stack <stack>          # 指定技術棧
claude-starter --list                   # 列出可用技術棧
claude-starter --force                  # 強制覆蓋既有檔案
claude-starter --target ../other        # 套用到其他資料夾

# 模板更新後
uv tool upgrade claude-starter

# 移除
uv tool uninstall claude-starter
```

要固定版本時，在網址後加 tag 或分支：`git+https://github.com/shannonchj/Claude-Starter@v0.1.0`。

### 不安裝、一次性執行

```bash
cd my-project
uvx --from git+https://github.com/shannonchj/Claude-Starter claude-starter --stack python-fastapi
```

### 舊用法（clone 本 repo 後執行，不需 uv）

```bash
python3 init.py --list
python3 init.py ../my-project                # 預設技術棧
python3 init.py <stack> ../my-project [--force]
```

### 會做哪些事

1. 複製 `core/` 全部內容到目標專案
2. 組合 `CLAUDE.md`：`CLAUDE.stack.md` 中與 `CLAUDE.base.md` 同名的 `##` 段落（「環境與指令」「目錄」）取代 base 的佔位內容，其他段落（「技術棧規則」）插入 `@@STACK@@` 位置
3. 組合 `REVIEW.md`：用 `stacks/<stack>/review-scope.txt` 取代 `review-scope` 區塊（沒有就用 core 的通用預設）
4. 合併 `core/.claude/settings.json` 與 `stacks/<stack>/settings.stack.json`（權限清單去重、hooks 依事件合併）
5. 複製 stack 的 `hooks/`、`skills/`、`agents/`（若有）到 `.claude/`
6. 合併 `core/.gitignore` 與 `stacks/<stack>/gitignore`，只追加目標專案缺少的規則
7. hooks 指令在 Windows 上產生為 `python -X utf8 ...`，其他平台為 `python3 -X utf8 ...`

## 初始化後的檢查清單

- [ ] 編輯 `CLAUDE.md`：替換所有 `<...>` 佔位內容，刪掉不適用的規則
- [ ] 在專案中啟動 Claude Code，執行 `/init` 讓它依實際程式碼補充或修正 CLAUDE.md（記得再人工審核）
- [ ] 填寫 `docs/architecture/overview.md`；新增其他文件時依 `docs/README.md` 的放置規則，並更新 `CLAUDE.md`「需要時再讀的文件」表格
- [ ] 調整 `docs/guides/ai-coding-guidelines.md` §2 專案特有禁止事項、§6 文件同步對照
- [ ] 調整 `REVIEW.md`：品質順序、專案特有的 Important 條件、不審查的目錄、`review-scope` 層級
- [ ] 使用 GitHub PR review：
  - 在 repo secrets 設定 `CLAUDE_CODE_OAUTH_TOKEN`（可用 `claude setup-token` 產生）
  - `REVIEW.md` 要合併進 main 後才生效（規則讀 base 分支）
  - 每個 PR 自動跑最多 3 輪；要再跑一輪時移除後重新加上 `claude-review` label
  - 要擋合併：在 branch protection 把 `summary` 設為 required check（有檔案沒審完時會失敗）
  - 改了 workflow 的 PR 本身不會被 review，改 workflow 要單獨開 PR
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
2. 填寫 `CLAUDE.stack.md` 的「環境與指令」「目錄」「技術棧規則」（標題要與 base 一致才會取代佔位）
3. 在 `settings.stack.json` 加入該技術棧的 `permissions.allow` 與 hooks
4. 在 `gitignore` 列出該技術棧的產物與快取；在 `review-scope.txt` 設定核心程式目錄與 lockfile
5. 在 `hooks/` 放格式化等腳本（參考 `python-fastapi/hooks/ruff_format.py`）
6. 需要時加入 `skills/`、`agents/` 子資料夾，`claude-starter` 會自動複製
7. 本機測試：`python3 init.py <new-stack> <暫存資料夾>`（直接讀 repo 內的模板，不用重新安裝）
8. 合併進 main 後，各台電腦執行 `uv tool upgrade claude-starter` 取得新模板；要發布固定版本時，更新 `src/claude_starter/__init__.py` 的 `__version__` 並打 git tag

## 節省 token 的原則（維護模板時請遵守）

- CLAUDE.md 控制在 100 行內，只寫 Claude 從程式碼看不出來的事；細節放 `docs/`，CLAUDE.md 只留「需要時再讀」的指標
- `@path` 引用會在**每次** session 載入；只有每次都需要的檔案才用 `@`，其餘寫成「需要時讀 docs/xxx.md」
- 流程性的說明放 skills（呼叫時才載入），不要塞進 CLAUDE.md
- linter / formatter 會處理的事不要寫成規則，交給 hooks
- 用 `/context` 檢查 memory files 佔比，超過 5–10% 就拆分
