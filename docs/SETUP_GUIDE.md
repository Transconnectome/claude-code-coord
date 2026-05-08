# Setup Guide — Step-by-Step Installation (단계별 설치 가이드)

This guide walks you through installing `/coord` from scratch. It is written for people who are comfortable with the command line but may not have used Claude Code's hook or MCP systems before.

이 가이드는 처음부터 `/coord`를 설치하는 과정을 안내합니다. 명령줄에 익숙하지만 Claude Code의 훅 또는 MCP 시스템을 사용해 본 적이 없는 분들을 위해 작성되었습니다.

---

## Prerequisites Checklist (사전 요구사항 체크리스트)

Complete all items before starting installation. (설치를 시작하기 전에 모든 항목을 완료하세요.)

- [ ] **Python 3.10 or higher** — `python3 --version` should print `3.10.x` or above (Python 3.10 이상)
- [ ] **Node.js 18 or higher** — `node --version` should print `v18.x.x` or above (Node.js 18 이상)
- [ ] **npm 9 or higher** — `npm --version` should print `9.x.x` or above (npm 9 이상)
- [ ] **Claude Code** — install from https://claude.ai/code and run `claude login` (Claude Code 설치 및 로그인)
- [ ] **TAVILY_API_KEY** — get a free key at https://app.tavily.com (무료 API 키 발급)
- [ ] **Git** — `git --version` (Git 설치 확인)
- [ ] (Optional) **OPENROUTER_API_KEY** — for premium model review in Stage 5 (선택적 — 프리미엄 모델 검토용)

---

## Step 1 — Clone the Repository (저장소 복사)

```bash
git clone https://github.com/Transconnectome/claude-code-coord.git
cd claude-code-coord
```

Verify the directory structure looks like this (디렉토리 구조 확인):

```
claude-code-coord/
├── .claude/                ← Framework files to copy (복사할 프레임워크 파일)
│   ├── CLAUDE.md
│   ├── hooks/              ← Anti-sycophancy hook scripts (아첨 방지 훅 스크립트)
│   ├── agents/             ← Specialist agent definitions (전문가 에이전트 정의)
│   └── memory/             ← Memory schema files (메모리 스키마 파일)
├── docs/                   ← Documentation (문서)
├── settings/
│   └── settings.json.template
└── tests/
```

---

## Step 2 — Back Up Your Existing .claude/ (기존 설정 백업)

If you already have a `~/.claude/` directory, back it up first to avoid overwriting your existing settings.

이미 `~/.claude/` 디렉토리가 있는 경우 기존 설정 덮어쓰기를 방지하기 위해 먼저 백업하세요.

```bash
# Check if ~/.claude/ exists (존재 여부 확인)
ls ~/.claude/ 2>/dev/null && echo "Found" || echo "Not found"

# Back it up if it exists (존재하는 경우 백업)
cp -r ~/.claude/ ~/.claude.backup.$(date +%Y%m%d)/
```

---

## Step 3 — Copy the Framework Files (프레임워크 파일 복사)

```bash
# From inside the claude-code-coord directory (claude-code-coord 디렉토리 내에서)
cp -r .claude/ ~/.claude/
```

Verify the copy succeeded (복사 성공 확인):

```bash
ls ~/.claude/
# Expected output (예상 출력):
# CLAUDE.md  agents/  hooks/  memory/
```

---

## Step 4 — Install MCP Servers (MCP 서버 설치)

Install each MCP server using npm. Some require additional configuration after installation.

npm을 사용하여 각 MCP 서버를 설치합니다. 일부는 설치 후 추가 구성이 필요합니다.

### Required servers (필수 서버)

```bash
# Multi-step reasoning engine (다단계 추론 엔진)
npm install -g @modelcontextprotocol/server-sequential-thinking

# Session key-value memory (세션 키-값 메모리)
npm install -g @modelcontextprotocol/server-memory
```

### Recommended servers (권장 서버)

```bash
# Real-time web search (실시간 웹 검색)
npm install -g @tavily/mcp-server

# Official library documentation (공식 라이브러리 문서)
npm install -g @upstash/context7-mcp

# UI component generation (UI 컴포넌트 생성)
npm install -g @21st-dev/magic

# Bulk pattern-based code edits (일괄 패턴 기반 코드 수정)
npm install -g morphllm-mcp
```

### Python-based servers (Python 기반 서버)

```bash
# Create a virtual environment (가상 환경 생성)
python3 -m venv ~/coord-env
source ~/coord-env/bin/activate

# Playwright browser automation (Playwright 브라우저 자동화)
pip install playwright-mcp
playwright install chromium

# NotebookLM document analysis (NotebookLM 문서 분석)
pip install notebooklm-mcp-cli
```

Verify all installations (모든 설치 확인):

```bash
# Check npm packages (npm 패키지 확인)
npm list -g --depth=0 | grep -E "(sequential|memory|tavily|context7|magic|morphllm)"

# Check python packages (Python 패키지 확인)
source ~/coord-env/bin/activate
pip list | grep -E "(playwright|notebooklm)"
```

---

## Step 5 — Configure settings.json (settings.json 구성)

Copy the template and fill in your API keys and paths.

템플릿을 복사하고 API 키와 경로를 입력합니다.

```bash
cp settings/settings.json.template ~/.claude/settings.json
```

Open `~/.claude/settings.json` in your editor and fill in:

편집기에서 `~/.claude/settings.json`을 열고 다음을 입력합니다:

```json
{
  "env": {
    "TAVILY_API_KEY": "tvly-YOUR_KEY_HERE",
    "OPENROUTER_API_KEY": "sk-or-YOUR_KEY_HERE"
  },
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "tavily": {
      "command": "npx",
      "args": ["-y", "@tavily/mcp-server"],
      "env": {
        "TAVILY_API_KEY": "tvly-YOUR_KEY_HERE"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "magic": {
      "command": "npx",
      "args": ["-y", "@21st-dev/magic"],
      "env": {
        "MAGIC_API_KEY": "YOUR_MAGIC_KEY_HERE"
      }
    },
    "playwright": {
      "command": "python3",
      "args": ["-m", "playwright_mcp"],
      "env": {
        "PATH": "/home/YOUR_USERNAME/coord-env/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

Replace every `YOUR_KEY_HERE` and `YOUR_USERNAME` with your actual values.

모든 `YOUR_KEY_HERE`와 `YOUR_USERNAME`을 실제 값으로 교체합니다.

---

## Step 6 — Configure Hook Paths (훅 경로 구성)

The anti-sycophancy hooks must point to the correct Python script paths. Add the `hooks` section to your `~/.claude/settings.json`:

아첨 방지 훅은 올바른 Python 스크립트 경로를 가리켜야 합니다. `~/.claude/settings.json`에 `hooks` 섹션을 추가합니다:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "python3 /home/YOUR_USERNAME/.claude/hooks/chavis_session_init.py"
      }
    ],
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "python3 /home/YOUR_USERNAME/.claude/hooks/chavis_prompt_classify.py"
      },
      {
        "type": "command",
        "command": "python3 /home/YOUR_USERNAME/.claude/hooks/chavis_strategic_challenge.py"
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python3 /home/YOUR_USERNAME/.claude/hooks/chavis_stop_audit.py"
      },
      {
        "type": "command",
        "command": "python3 /home/YOUR_USERNAME/.claude/hooks/chavis_persistent_logger.py"
      }
    ]
  }
}
```

Replace `YOUR_USERNAME` with your actual home directory username (실제 사용자 이름으로 교체):

```bash
# Find your username (사용자 이름 확인)
whoami
```

---

## Step 7 — Initialize the Memory Directories (메모리 디렉토리 초기화)

The hook system writes to specific directories that must exist before the first session.

훅 시스템은 첫 번째 세션 전에 존재해야 하는 특정 디렉토리에 씁니다.

```bash
# Create anti-sycophancy memory directories (아첨 방지 메모리 디렉토리 생성)
mkdir -p ~/.claude/projects/-home-$(whoami)/memory/sycophancy/lessons/
mkdir -p /tmp/chavis/

# Create the initial pattern library (초기 패턴 라이브러리 생성)
touch ~/.claude/projects/-home-$(whoami)/memory/sycophancy/pattern_library.md
touch ~/.claude/projects/-home-$(whoami)/memory/sycophancy/session_log.jsonl
touch ~/.claude/projects/-home-$(whoami)/memory/sycophancy/calibration_log.jsonl

# Create the MEMORY.md index (MEMORY.md 인덱스 생성)
touch ~/.claude/projects/-home-$(whoami)/memory/MEMORY.md
```

---

## Step 8 — Verify the Installation (설치 검증)

Run the test suite to confirm everything is working.

테스트 스위트를 실행하여 모든 것이 작동하는지 확인합니다.

```bash
cd claude-code-coord/tests/

# Run hook system unit tests (훅 시스템 단위 테스트 실행)
python3 -m pytest test_hooks.py -v

# Run a quick end-to-end smoke test (빠른 엔드-투-엔드 스모크 테스트)
claude code --print "/coord 'This is a setup verification test. Reply with COORD_OK.'"
```

Expected output for the smoke test (스모크 테스트 예상 출력):

```
COORD_OK
```

If you see `COORD_OK`, the installation succeeded (설치 성공).

---

## Troubleshooting (문제 해결)

### Problem: MCP server not found (MCP 서버를 찾을 수 없음)

```
Error: Cannot find module '@modelcontextprotocol/server-sequential-thinking'
```

**Fix (해결):** The npm package was not installed globally. Re-run:

```bash
npm install -g @modelcontextprotocol/server-sequential-thinking
# Verify (확인)
npx -y @modelcontextprotocol/server-sequential-thinking --version
```

---

### Problem: Hook script permission denied (훅 스크립트 권한 거부)

```
Error: Permission denied: ~/.claude/hooks/chavis_session_init.py
```

**Fix (해결):**

```bash
chmod +x ~/.claude/hooks/chavis_*.py
```

---

### Problem: Tavily API key rejected (Tavily API 키 거부)

```
Error: TAVILY_API_KEY is invalid or expired
```

**Fix (해결):** Get a new key at https://app.tavily.com. Paste it in both the `env` top-level and the `tavily` mcpServer `env` in `~/.claude/settings.json`.

새 키를 https://app.tavily.com에서 발급받으세요. `~/.claude/settings.json`의 최상위 `env`와 `tavily` mcpServer `env` 모두에 붙여넣습니다.

---

### Problem: Playwright browser not found (Playwright 브라우저를 찾을 수 없음)

```
Error: browserType.launch: Executable doesn't exist at …/chromium
```

**Fix (해결):**

```bash
source ~/coord-env/bin/activate
playwright install chromium
```

---

### Problem: Memory directory write error (메모리 디렉토리 쓰기 오류)

```
FileNotFoundError: [Errno 2] No such file or directory:
  '~/.claude/projects/-home-username/memory/sycophancy/session_log.jsonl'
```

**Fix (해결):** Re-run Step 7 with your correct username substituted.

Step 7을 올바른 사용자 이름으로 대체하여 다시 실행합니다.

---

### Problem: Claude Code does not recognize /coord (Claude Code가 /coord를 인식하지 못함)

The `/coord` system is a skill registered in `~/.claude/CLAUDE.md`. If it is not working, verify the file was copied correctly.

`/coord` 시스템은 `~/.claude/CLAUDE.md`에 등록된 스킬입니다. 작동하지 않으면 파일이 올바르게 복사되었는지 확인합니다.

```bash
# Check CLAUDE.md exists and contains coord (CLAUDE.md 존재 및 coord 포함 확인)
grep -l "coord" ~/.claude/CLAUDE.md && echo "Found" || echo "Missing — re-run Step 3"
```

---

## Quick Verification Checklist (빠른 검증 체크리스트)

After completing all steps, verify each item:

모든 단계를 완료한 후 각 항목을 확인합니다:

- [ ] `~/.claude/CLAUDE.md` exists and contains `/coord` (존재 및 /coord 포함)
- [ ] `~/.claude/settings.json` has your API keys and hook paths (API 키 및 훅 경로 포함)
- [ ] `~/.claude/hooks/chavis_*.py` files exist and are executable (실행 가능한 훅 파일)
- [ ] `~/.claude/projects/-home-USERNAME/memory/sycophancy/` directory exists (디렉토리 존재)
- [ ] `npx -y @modelcontextprotocol/server-sequential-thinking` runs without error (오류 없이 실행)
- [ ] Smoke test returns `COORD_OK` (스모크 테스트 통과)

If all items are checked, your installation is complete. (모든 항목이 확인되면 설치가 완료되었습니다.)
