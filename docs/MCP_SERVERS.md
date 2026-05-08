# MCP Servers Reference (MCP 서버 참조)

This document describes each of the 9 MCP servers used by the `/coord` pipeline: purpose, installation, JSON configuration block, API key requirements, and fallback behavior.

이 문서는 `/coord` 파이프라인에서 사용하는 9개의 MCP 서버 각각을 설명합니다: 목적, 설치, JSON 구성 블록, API 키 요구사항, 대체 동작.

---

## How MCP Servers Fit into the Pipeline (MCP 서버가 파이프라인에서의 역할)

MCP (Model Context Protocol) servers extend Claude Code with specialized capabilities. The pipeline activates the appropriate server based on task type — it does not run all servers for every task.

MCP(Model Context Protocol) 서버는 Claude Code를 전문화된 기능으로 확장합니다. 파이프라인은 작업 유형에 따라 적절한 서버를 활성화합니다 — 모든 작업에 대해 모든 서버를 실행하지 않습니다.

| Stage (단계) | MCP servers typically active (일반적으로 활성화되는 MCP 서버) |
|-------------|-------------------------------------------------------------|
| Stage 1 — Memory | `memory`, `serena`, `graphiti-memory` |
| Stage 2 — Plan | `sequential-thinking` |
| Stage 3 — Research | `tavily`, `context7`, `playwright`, `notebooklm` |
| Stage 4 — Execute | `magic`, `morphllm`, `serena` |
| Stage 5 — Review | `sequential-thinking` |
| Stage 6 — Memory | `memory`, `serena`, `graphiti-memory` |

---

## 1. sequential-thinking (순차적 사고)

**Purpose:** Multi-step structured reasoning with hypothesis testing and self-reflection. The primary reasoning engine for the Plan stage and complex debugging. Best when a problem has 3 or more interconnected components.

**목적:** 가설 테스트 및 자기 반성이 있는 다단계 구조화된 추론. 계획 단계와 복잡한 디버깅을 위한 기본 추론 엔진.

**When active (활성화 시점):** Stage 2 (Plan), Stage 5 (Review), and any task with `--think`, `--think-hard`, or `--ultrathink` flags.

**Installation (설치):**
```bash
npm install -g @modelcontextprotocol/server-sequential-thinking
```

**Configuration (구성):**
```json
"sequential-thinking": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
}
```

**API key required:** No (API 키 불필요)

**Fallback (대체):** Native Claude reasoning — slower for multi-component problems but functional for simple analysis. (네이티브 Claude 추론 — 다중 구성 요소 문제에는 느리지만 단순 분석에는 기능적)

---

## 2. memory (세션 메모리)

**Purpose:** Key-value session persistence. Stores plan checkpoints, task completion status, and short-term session context. Data persists within a session but does not cross session boundaries.

**목적:** 키-값 세션 지속성. 계획 체크포인트, 작업 완료 상태, 단기 세션 컨텍스트를 저장합니다. 데이터는 세션 내에서 지속되지만 세션 경계를 넘지 않습니다.

**When active (활성화 시점):** Stage 1 (read), Stage 2 (write plan), Stage 4 (checkpoints), Stage 6 (final write).

**Installation (설치):**
```bash
npm install -g @modelcontextprotocol/server-memory
```

**Configuration (구성):**
```json
"memory": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"]
}
```

**API key required:** No (API 키 불필요)

**Fallback (대체):** Claude's in-context memory — lost when context window closes or compacts. For cross-session persistence, use auto-memory files instead. (Claude 인컨텍스트 메모리 — 컨텍스트 창이 닫히거나 압축될 때 소실)

---

## 3. tavily (웹 검색)

**Purpose:** Real-time web search with structured results, domain filtering, and time-range filtering. Supports academic search mode for scholarly content. The primary tool when information from after the model's knowledge cutoff is needed.

**목적:** 구조화된 결과, 도메인 필터링, 시간 범위 필터링이 있는 실시간 웹 검색. 학술 콘텐츠를 위한 학술 검색 모드 지원.

**When active (활성화 시점):** Stage 3 (Research), on-demand for current information queries.

**Installation (설치):**
```bash
npm install -g @tavily/mcp-server
```

**Configuration (구성):**
```json
"tavily": {
  "command": "npx",
  "args": ["-y", "@tavily/mcp-server"],
  "env": {
    "TAVILY_API_KEY": "tvly-YOUR_KEY_HERE"
  }
}
```

**API key required:** Yes — get a free key at https://app.tavily.com (무료 키 발급 필요)

**Search modes available (사용 가능한 검색 모드):**

| Mode (모드) | Flag (플래그) | Best for (최적 용도) |
|------------|--------------|---------------------|
| General web | default | News, tutorials, blog posts |
| Academic | `search_depth="advanced"` | Research papers, citations |
| News | `topic="news"` | Recent events, announcements |
| Domain-specific | `include_domains=[…]` | Authoritative sources only |

**Fallback (대체):** Native `WebSearch` tool — less structured but functional. (네이티브 `WebSearch` 도구 — 덜 구조화되어 있지만 기능적)

---

## 4. context7 (공식 라이브러리 문서)

**Purpose:** Curated, version-specific documentation lookup for libraries and frameworks. Returns official documentation patterns rather than web search approximations. Eliminates hallucinated API signatures.

**목적:** 라이브러리와 프레임워크를 위한 큐레이션된 버전별 문서 조회. 웹 검색 근사값이 아닌 공식 문서 패턴을 반환합니다.

**When active (활성화 시점):** Stage 3 (Research) when import statements, framework names, or library-specific questions are detected.

**Installation (설치):**
```bash
npm install -g @upstash/context7-mcp
```

**Configuration (구성):**
```json
"context7": {
  "command": "npx",
  "args": ["-y", "@upstash/context7-mcp"]
}
```

**API key required:** No (API 키 불필요)

**Supported library categories (지원 라이브러리 범주):**
- Frontend frameworks: React, Vue, Angular, Next.js, Svelte (프론트엔드 프레임워크)
- Backend frameworks: Express, FastAPI, Django, Rails (백엔드 프레임워크)
- Databases: PostgreSQL, MongoDB, Redis, Prisma (데이터베이스)
- Cloud SDKs: AWS, GCP, Azure, Vercel (클라우드 SDK)
- ML libraries: PyTorch, scikit-learn, Hugging Face (ML 라이브러리)

**Fallback (대체):** Tavily web search targeting official docs domains. (공식 문서 도메인을 타겟팅하는 Tavily 웹 검색)

---

## 5. magic (UI 컴포넌트 생성)

**Purpose:** Modern, accessible UI component generation using patterns from 21st.dev. Produces production-ready React components with Tailwind CSS, proper ARIA attributes, and responsive design.

**목적:** 21st.dev의 패턴을 사용한 현대적이고 접근 가능한 UI 컴포넌트 생성. Tailwind CSS, 적절한 ARIA 속성, 반응형 디자인이 있는 프로덕션 준비 React 컴포넌트를 생성합니다.

**When active (활성화 시점):** Stage 4 (Execute) when UI component requests are detected, or on `/ui` or `/21` commands.

**Installation (설치):**
```bash
npm install -g @21st-dev/magic
```

**Configuration (구성):**
```json
"magic": {
  "command": "npx",
  "args": ["-y", "@21st-dev/magic"],
  "env": {
    "MAGIC_API_KEY": "YOUR_MAGIC_KEY_HERE"
  }
}
```

**API key required:** Yes — get a key at https://21st.dev (API 키 필요)

**Component types supported (지원하는 컴포넌트 유형):**
- Forms, input fields, validation (폼, 입력 필드, 검증)
- Navigation: navbar, sidebar, breadcrumbs (네비게이션)
- Data display: tables, cards, charts (데이터 표시)
- Feedback: modals, toasts, alerts (피드백)
- Layout: grids, containers, responsive wrappers (레이아웃)

**Fallback (대체):** Manual HTML/CSS with Claude native generation — functional but less polished. (네이티브 Claude HTML/CSS 생성 — 기능적이지만 덜 세련됨)

---

## 6. playwright (브라우저 자동화)

**Purpose:** Real browser automation for E2E testing, visual validation, screenshot capture, and accessibility auditing. Uses Chromium by default. The only tool that can verify rendered output, not just source code.

**목적:** E2E 테스트, 시각적 검증, 스크린샷 캡처, 접근성 감사를 위한 실제 브라우저 자동화. 기본적으로 Chromium 사용.

**When active (활성화 시점):** Stage 3 (complex page extraction) and Stage 5 (visual validation), on demand for browser testing.

**Installation (설치):**
```bash
# Using pip (pip 사용)
pip install playwright-mcp
playwright install chromium

# Or using npm (npm 사용)
npm install -g @playwright/mcp
```

**Configuration (구성):**
```json
"playwright": {
  "command": "python3",
  "args": ["-m", "playwright_mcp"],
  "env": {
    "PATH": "/home/YOUR_USERNAME/coord-env/bin:/usr/local/bin:/usr/bin:/bin"
  }
}
```

**API key required:** No (API 키 불필요)

**Capabilities (기능):**

| Task (작업) | Playwright tool (Playwright 도구) |
|------------|----------------------------------|
| Navigate to a URL | `browser_navigate` |
| Click an element | `browser_click` |
| Fill a form | `browser_fill_form` |
| Take a screenshot | `browser_take_screenshot` |
| Read console errors | `browser_console_messages` |
| Test accessibility | `browser_snapshot` (ARIA tree) |
| Run custom JavaScript | `browser_evaluate` |

**Fallback (대체):** Tavily for content extraction, manual testing instructions for E2E scenarios. (콘텐츠 추출은 Tavily, E2E 시나리오는 수동 테스트 지침)

---

## 7. morphllm (일괄 패턴 편집)

**Purpose:** Pattern-based code editing engine with token optimization. Makes consistent changes across multiple files using natural language edit instructions. 30–50% more token-efficient than individual Edit calls.

**목적:** 토큰 최적화가 있는 패턴 기반 코드 편집 엔진. 자연어 편집 지시를 사용하여 여러 파일에 걸쳐 일관된 변경을 수행합니다.

**When active (활성화 시점):** Stage 4 (Execute) when bulk transformations, style enforcement, or framework migrations are planned.

**Installation (설치):**
```bash
npm install -g morphllm-mcp
```

**Configuration (구성):**
```json
"morphllm": {
  "command": "npx",
  "args": ["-y", "morphllm-mcp"]
}
```

**API key required:** No (API 키 불필요)

**Best use cases (최적 사용 사례):**
- Replace all `console.log` with structured logger calls (모든 console.log를 구조화된 로거 호출로 교체)
- Enforce ESLint rules across a large codebase (대규모 코드베이스에 ESLint 규칙 적용)
- Update React class components to function components (React 클래스 컴포넌트를 함수 컴포넌트로 업데이트)
- Apply consistent error handling pattern across all endpoints (모든 엔드포인트에 일관된 오류 처리 패턴 적용)

**When NOT to use morphllm (morphllm을 사용하지 말아야 할 경우):** Symbol renames with dependency tracking — use `serena` instead. Complex semantic changes — use individual edits.

**Fallback (대체):** MultiEdit tool with multiple individual Edit calls. (여러 개별 Edit 호출이 있는 MultiEdit 도구)

---

## 8. serena (시맨틱 코드 탐색)

**Purpose:** Semantic code understanding with LSP integration. Handles symbol operations (rename, extract, find references), dependency tracking, and cross-session project memory. The primary tool for understanding large, multi-language codebases.

**목적:** LSP 통합이 있는 시맨틱 코드 이해. 심볼 조작(이름 변경, 추출, 참조 찾기), 의존성 추적, 세션 간 프로젝트 메모리를 처리합니다.

**When active (활성화 시점):** Stage 1 (memory read), Stage 3 (codebase exploration), Stage 4 (symbol operations), Stage 6 (memory write).

**Installation (설치):**
Serena is typically available as part of Claude Code's MCP ecosystem. Check your current installation:

Serena는 일반적으로 Claude Code의 MCP 생태계의 일부로 제공됩니다. 현재 설치를 확인하세요:

```bash
claude mcp list | grep serena
```

If not installed (설치되지 않은 경우):
```bash
npm install -g @serena-ai/mcp
```

**Configuration (구성):**
```json
"serena": {
  "command": "npx",
  "args": ["-y", "@serena-ai/mcp"],
  "env": {
    "WORKSPACE_PATH": "/path/to/your/project"
  }
}
```

**API key required:** No (API 키 불필요)

**Key operations (주요 작업):**

| Operation (작업) | Tool (도구) |
|-----------------|------------|
| List stored memories | `list_memories()` |
| Read a memory | `read_memory("key")` |
| Write a memory | `write_memory("key", value)` |
| Delete a memory | `delete_memory("key")` |
| Find a symbol | `find_symbol("functionName")` |
| Find all references | `find_referencing_symbols("ClassName")` |
| Find declaration | `find_declaration("variableName")` |

**Fallback (대체):** Grep for code search, manual file reads for structure discovery. (코드 검색은 Grep, 구조 발견은 수동 파일 읽기)

---

## 9. notebooklm (문서 분석)

**Purpose:** Deep analysis of long-form documents using Google NotebookLM's knowledge base capabilities. Best for research papers, lengthy technical specifications, and document collections that exceed Claude's context window.

**목적:** Google NotebookLM의 지식 베이스 기능을 사용한 장형 문서의 심층 분석. 연구 논문, 긴 기술 사양, Claude의 컨텍스트 창을 초과하는 문서 컬렉션에 최적입니다.

**When active (활성화 시점):** Stage 3 (Research) when document ingestion is required, or explicitly when user provides a long document for analysis.

**Installation (설치):**
```bash
pip install notebooklm-mcp-cli
```

**Verify (확인):**
```bash
nlm --version
```

**Configuration (구성):**
```json
"notebooklm": {
  "command": "python3",
  "args": ["-m", "notebooklm_tools.mcp.server"],
  "env": {
    "PATH": "/home/YOUR_USERNAME/coord-env/bin:/usr/local/bin:/usr/bin:/bin"
  }
}
```

**Authentication (인증):** Requires Google account authorization. Run `nlm login` in a terminal after installation.

Google 계정 인증이 필요합니다. 설치 후 터미널에서 `nlm login`을 실행합니다.

**API key required:** No — uses Google account OAuth (API 키 불필요 — Google 계정 OAuth 사용)

**Key capabilities (주요 기능):**

| Task (작업) | Tool (도구) |
|------------|------------|
| Create a new notebook | `notebook_create` |
| Add a source document | `source_add` |
| Query the knowledge base | `notebook_query` |
| Cross-notebook analysis | `cross_notebook_query` |
| Generate audio overview | `studio_create(artifact_type="audio")` |

**Fallback (대체):** Reading large documents directly with the Read tool + sequential summarization. Slower for very long documents but always available. (Read 도구로 직접 읽기 + 순차 요약 — 매우 긴 문서에는 느리지만 항상 사용 가능)

---

## Graphiti Memory (graphiti-memory)

**Purpose:** Long-term domain knowledge graph. Stores temporally-aware facts, research decisions, meeting records, and experimental results as a queryable knowledge graph. Unlike the `memory` server, Graphiti persists across sessions and months.

**목적:** 장기 도메인 지식 그래프. 시간 인식 사실, 연구 결정, 회의록, 실험 결과를 쿼리 가능한 지식 그래프로 저장합니다. `memory` 서버와 달리 Graphiti는 세션과 달을 넘어 지속됩니다.

**When active (활성화 시점):** Stage 1 (knowledge retrieval), Stage 6 (knowledge storage), when `search_nodes` or `add_memory` operations are needed.

**Installation (설치):**
```bash
pip install graphiti-core
# Set up the database backend (데이터베이스 백엔드 설정)
# See: https://github.com/getzep/graphiti
```

**Configuration (구성):**
```json
"graphiti-memory": {
  "command": "python3",
  "args": ["-m", "graphiti_mcp.server"],
  "env": {
    "OPENROUTER_API_KEY": "sk-or-YOUR_KEY_HERE",
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USER": "neo4j",
    "NEO4J_PASSWORD": "YOUR_DB_PASSWORD"
  }
}
```

**API key required:** Yes — requires `OPENROUTER_API_KEY` for embeddings, and Neo4j for the graph database.

임베딩을 위한 `OPENROUTER_API_KEY`와 그래프 데이터베이스를 위한 Neo4j가 필요합니다.

**Key operations (주요 작업):**

| Operation (작업) | Tool (도구) |
|-----------------|------------|
| Store a fact or event | `add_memory` |
| Search for entities | `search_nodes` |
| Search for relationships | `search_memory_facts` |
| Get recent episodes | `get_episodes` |
| Delete outdated fact | `delete_entity_edge` |

**Important note (중요 참고사항):** If Graphiti is unavailable (database not running, API key missing), the pipeline falls back gracefully to auto-memory only. A warning is logged to `/tmp/chavis/session_init.log`.

Graphiti를 사용할 수 없는 경우(데이터베이스 미실행, API 키 누락), 파이프라인은 자동으로 auto-memory 전용으로 대체됩니다.

**Fallback (대체):** Auto-memory files at `~/.claude/projects/-home-USERNAME/memory/`. Less queryable but always available. (자동 메모리 파일 — 쿼리 가능성은 낮지만 항상 사용 가능)

---

## Complete settings.json MCP Block (완전한 settings.json MCP 블록)

The following is the full `mcpServers` configuration block with all 9 servers. Copy it into `~/.claude/settings.json` and replace placeholder values.

다음은 9개 서버 모두가 있는 전체 `mcpServers` 구성 블록입니다. `~/.claude/settings.json`에 복사하고 플레이스홀더 값을 교체합니다.

```json
{
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
    },
    "morphllm": {
      "command": "npx",
      "args": ["-y", "morphllm-mcp"]
    },
    "serena": {
      "command": "npx",
      "args": ["-y", "@serena-ai/mcp"]
    },
    "notebooklm": {
      "command": "python3",
      "args": ["-m", "notebooklm_tools.mcp.server"],
      "env": {
        "PATH": "/home/YOUR_USERNAME/coord-env/bin:/usr/local/bin:/usr/bin:/bin"
      }
    },
    "graphiti-memory": {
      "command": "python3",
      "args": ["-m", "graphiti_mcp.server"],
      "env": {
        "OPENROUTER_API_KEY": "sk-or-YOUR_KEY_HERE",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "YOUR_DB_PASSWORD"
      }
    }
  }
}
```
