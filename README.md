# coord — Intelligent Complex Task Workflow

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Node.js 18+](https://img.shields.io/badge/Node.js-18%2B-green.svg)](https://nodejs.org/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-required-purple.svg)](https://claude.ai/code)

`/coord` is a 6-stage pipeline built on top of Claude Code that orchestrates memory retrieval, planning, parallel research, specialist agent delegation, and anti-sycophancy verification for complex engineering and research tasks.

`/coord`는 메모리 검색, 계획 수립, 병렬 리서치, 전문가 에이전트 위임, 아첨 방지 검증을 조율하는 6단계 파이프라인입니다.

---

## Quick Start (빠른 시작)

```bash
# Step 1 — Clone this repository (저장소 복사)
git clone https://github.com/Transconnectome/claude-code-coord.git
cd claude-code-coord

# Step 2 — Copy framework files (프레임워크 파일 복사)
cp -r .claude/ ~/.claude/

# Step 3 — Install MCP servers, then verify (MCP 서버 설치 및 검증)
npm install -g @modelcontextprotocol/server-sequential-thinking
claude code --print "/coord 'Hello, is this working?'"
```

Full installation details: [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md)

---

## Architecture (아키텍처)

### 6-Stage Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                   /coord — 6-Stage Pipeline                         │
├──────────┬──────────────────────────────────────────────────────────┤
│  Stage 0 │  BOOTSTRAP — detect task complexity, choose mode         │
│  준비     │  (작업 복잡도 측정, 실행 모드 선택)                         │
├──────────┼──────────────────────────────────────────────────────────┤
│  Stage 1 │  MEMORY PRE-CHECK — parallel 3-source scan               │
│  메모리   │  Auto-memory ‖ Serena MCP ‖ Graphiti knowledge graph     │
├──────────┼──────────────────────────────────────────────────────────┤
│  Stage 2 │  PLAN — sequential-thinking MCP + parallelization map    │
│  계획     │  (다단계 추론 + 병렬화 가능한 작업 분리)                     │
├──────────┼──────────────────────────────────────────────────────────┤
│  Stage 3 │  RESEARCH — parallel subagents (Explore ‖ web ‖ docs)   │
│  리서치   │  (탐색/웹/공식문서 서브에이전트 병렬 실행)                    │
├──────────┼──────────────────────────────────────────────────────────┤
│  Stage 4 │  EXECUTE — specialist agents + intermediate validation   │
│  실행     │  (전문가 에이전트 + 단계별 검증)                            │
├──────────┼──────────────────────────────────────────────────────────┤
│  Stage 5 │  REVIEW — critic agent + optional premium model review   │
│  리뷰     │  (critic 에이전트 + 선택적 프리미엄 모델 검토)               │
├──────────┼──────────────────────────────────────────────────────────┤
│  Stage 6 │  MEMORY UPDATE — route lessons to correct store          │
│  메모리   │  Auto-memory > Graphiti > Serena, update MEMORY.md       │
└──────────┴──────────────────────────────────────────────────────────┘
```

### Memory Layer (메모리 계층)

The pipeline always reads from three memory sources **in parallel** before planning. Each source serves a distinct purpose.

파이프라인은 계획 전에 항상 세 가지 메모리 소스를 **병렬**로 읽습니다.

| Source | What it stores (저장 내용) | Persistence (지속성) |
|--------|--------------------------|---------------------|
| **Auto-memory** (`~/.claude/projects/…/memory/`) | User preferences, session lessons, project state (사용자 선호, 세션 교훈, 프로젝트 상태) | Cross-session (세션 간) |
| **Serena MCP** | Code symbols, file locations, workspace structure (코드 심볼, 파일 위치, 워크스페이스 구조) | Within session + project (세션 내 + 프로젝트) |
| **Graphiti** (`graphiti-memory`) | Domain knowledge, research decisions, meeting records (도메인 지식, 연구 결정, 회의록) | Long-term knowledge graph (장기 지식 그래프) |

### MCP Tool Mapping Table (MCP 도구 매핑)

| Task type (작업 유형) | Primary MCP | Fallback |
|----------------------|------------|---------|
| Multi-step reasoning (다단계 추론) | `sequential-thinking` | Native Claude |
| Web search (웹 검색) | `tavily` | `WebSearch` |
| Official library docs (공식 문서) | `context7` | Tavily |
| UI component generation (UI 생성) | `magic` | Manual HTML |
| Browser automation (브라우저 자동화) | `playwright` | Manual testing |
| Symbol operations (심볼 조작) | `serena` | Grep + Edit |
| Bulk pattern edits (일괄 패턴 편집) | `morphllm` | MultiEdit |
| Document analysis (문서 분석) | `notebooklm` | Read + summarize |
| Knowledge graph memory (지식 그래프) | `graphiti-memory` | Auto-memory |

---

## Installation (설치)

### Prerequisites (사전 요구사항)

- Python 3.10 or higher (Python 3.10 이상)
- Node.js 18 or higher (Node.js 18 이상)
- [Claude Code](https://claude.ai/code) installed and authenticated (설치 및 인증 완료)
- API keys: `TAVILY_API_KEY`, `OPENROUTER_API_KEY` (optional for premium review) (선택적 — 프리미엄 리뷰용)

### Step-by-Step (단계별 설치)

**1. Clone the repository (저장소 복사)**

```bash
git clone https://github.com/Transconnectome/claude-code-coord.git
cd claude-code-coord
```

**2. Copy the `.claude/` framework directory (프레임워크 디렉토리 복사)**

```bash
# Back up your existing ~/.claude/ first (기존 설정 백업 권장)
cp -r ~/.claude/ ~/.claude.backup/

cp -r .claude/ ~/.claude/
```

**3. Install MCP servers (MCP 서버 설치)**

```bash
# Required servers (필수 서버)
npm install -g @modelcontextprotocol/server-sequential-thinking
npm install -g @modelcontextprotocol/server-memory

# Recommended servers (권장 서버)
npm install -g @tavily/mcp-server
npm install -g @21st-dev/magic
```

Full MCP installation instructions: [`docs/MCP_SERVERS.md`](docs/MCP_SERVERS.md)

**4. Copy and configure settings (설정 파일 구성)**

```bash
cp settings/settings.json.template ~/.claude/settings.json
# Edit ~/.claude/settings.json — fill in API keys and hook paths
# ~/.claude/settings.json 편집 — API 키 및 hook 경로 입력
```

**5. Verify the installation (설치 검증)**

```bash
cd tests/
python -m pytest test_hooks.py -v
```

---

## Usage (사용법)

### Basic invocation (기본 호출)

```bash
# Explicit invocation (명시적 호출)
/coord "Implement JWT authentication for the FastAPI service"

# With @sub shorthand (백그라운드 에이전트 단축 호출)
@sub Implement JWT authentication for the FastAPI service
```

### Auto-activation keywords (자동 활성화 키워드)

`/coord` activates automatically when the user message contains signals of complexity. You do not need to type `/coord` explicitly.

복잡성 신호가 포함된 메시지에서는 `/coord`를 명시적으로 입력하지 않아도 자동 활성화됩니다.

| Signal category (신호 범주) | Example keywords (예시 키워드) |
|----------------------------|-------------------------------|
| Scope ambiguity (범위 모호) | "not sure", "thinking about", "explore" |
| Multi-domain (다중 도메인) | "frontend + backend", "infra and code" |
| Long pipelines (긴 파이프라인) | "step by step", "refactor the whole", "migrate" |
| Debugging (디버깅) | "figure out why", "root cause", "broken since" |
| Architecture (아키텍처) | "design a system", "how should I structure" |
| Research (리서치) | "find the best", "compare approaches", "survey" |

### When NOT to use /coord (사용하지 말아야 할 경우)

- Simple one-file edits (단순 단일 파일 수정)
- Quick factual questions (빠른 사실 질문)
- Single-tool operations under 3 steps (3단계 미만 단일 도구 작업)
- Casual conversation (일상적인 대화)

For detailed use-case guidance: [`docs/WHEN_TO_USE.md`](docs/WHEN_TO_USE.md)

---

## MCP Servers (MCP 서버)

| Server | Role (역할) | API key required (API 키 필요) |
|--------|------------|-------------------------------|
| `sequential-thinking` | Multi-step structured reasoning (다단계 구조적 추론) | No |
| `memory` | Key-value session persistence (세션 내 키-값 저장) | No |
| `tavily` | Real-time web search (실시간 웹 검색) | Yes — `TAVILY_API_KEY` |
| `context7` | Official library documentation (공식 라이브러리 문서) | No |
| `magic` | UI component generation via 21st.dev (UI 컴포넌트 생성) | Yes — `MAGIC_API_KEY` |
| `playwright` | Browser automation and E2E testing (브라우저 자동화) | No |
| `morphllm` | Bulk pattern-based code edits (일괄 패턴 기반 코드 수정) | No |
| `serena` | Semantic code navigation and memory (시맨틱 코드 탐색) | No |
| `notebooklm` | Document analysis and knowledge base (문서 분석 + 지식 베이스) | No (Google auth) |

Full per-server documentation: [`docs/MCP_SERVERS.md`](docs/MCP_SERVERS.md)

---

## Hook System — Anti-Sycophancy (훅 시스템 — 아첨 방지)

The hook system runs Python scripts at four Claude Code lifecycle events. It catches agreement bias before responses are generated and after they complete.

훅 시스템은 Claude Code 수명 주기의 네 이벤트에서 Python 스크립트를 실행합니다. 응답이 생성되기 전과 후 모두에서 동의 편향을 감지합니다.

| Hook event | Script | Purpose (역할) |
|-----------|--------|----------------|
| `SessionStart` | `chavis_session_init.py` | Load sycophancy lessons from prior sessions (이전 세션 교훈 로드) |
| `UserPromptSubmit` | `chavis_prompt_classify.py` | Classify risk level of incoming prompt (프롬프트 위험 수준 분류) |
| `UserPromptSubmit` | `chavis_strategic_challenge.py` | Fire Strategic Challenge Template on scope pivots (범위 피봇 시 전략 도전 템플릿 생성) |
| `Stop` | `chavis_stop_audit.py` | Audit completed response for compliance drift (완료된 응답의 규정 준수 편차 감사) |
| `Stop` | `chavis_persistent_logger.py` | Append evaluation to audit trail (감사 추적에 평가 추가) |

Full hook documentation: [`docs/HOOKS.md`](docs/HOOKS.md)

---

## Agents (에이전트)

Specialist agents are delegated via `subagent_type`. The pipeline selects the right agent automatically based on task classification.

전문가 에이전트는 `subagent_type`을 통해 위임됩니다. 파이프라인은 작업 분류를 기반으로 자동으로 적절한 에이전트를 선택합니다.

| Agent | When activated (활성화 시점) |
|-------|------------------------------|
| `explore` | Codebase discovery, 3+ search queries (코드베이스 탐색) |
| `plan` | Implementation strategy before coding (코딩 전 구현 전략) |
| `deep-research-agent` | Multi-source web research + synthesis (다중 소스 웹 리서치) |
| `critic` | Review and falsifiability challenge (검토 및 반증 가능성 도전) |
| `backend-architect` | Server-side system design (서버 사이드 시스템 설계) |
| `frontend-architect` | UI/UX architecture decisions (UI/UX 아키텍처 결정) |
| `python-expert` | Python-specific implementation (Python 특화 구현) |
| `quality-engineer` | Test coverage and quality gates (테스트 커버리지 및 품질 게이트) |
| `security-engineer` | Threat modeling and vulnerability review (위협 모델링 및 취약점 검토) |
| `performance-engineer` | Profiling and optimization (프로파일링 및 최적화) |
| `technical-writer` | Documentation and user guides (문서화 및 사용자 가이드) |
| `requirements-analyst` | Ambiguous request clarification (모호한 요청 명세화) |
| `system-architect` | Full system design across domains (전체 시스템 설계) |
| `sci-method` | Scientific hypothesis-evidence-validation workflow (과학적 가설-증거-검증 워크플로우) |

Full agent documentation: [`docs/AGENTS.md`](docs/AGENTS.md)

---

## Testing (테스트)

```bash
cd tests/
python -m pytest test_hooks.py -v          # Hook system unit tests (훅 시스템 단위 테스트)
python -m pytest test_pipeline.py -v       # 6-stage pipeline integration tests (파이프라인 통합 테스트)
python -m pytest test_agents.py -v         # Agent routing tests (에이전트 라우팅 테스트)
```

---

## Documentation Index (문서 인덱스)

| File | Contents |
|------|----------|
| [`docs/WORKFLOW.md`](docs/WORKFLOW.md) | 6-stage pipeline deep dive (6단계 파이프라인 상세) |
| [`docs/AGENTS.md`](docs/AGENTS.md) | All specialist agents with examples (전문가 에이전트 목록 및 예시) |
| [`docs/HOOKS.md`](docs/HOOKS.md) | Anti-sycophancy hook architecture (아첨 방지 훅 아키텍처) |
| [`docs/WHEN_TO_USE.md`](docs/WHEN_TO_USE.md) | Use-case guide with scenarios (사용 케이스 가이드) |
| [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md) | Step-by-step installation for beginners (초보자용 설치 가이드) |
| [`docs/MCP_SERVERS.md`](docs/MCP_SERVERS.md) | Per-server configuration reference (서버별 설정 참조) |

---

## License

MIT License. See [LICENSE](LICENSE) for full text.
