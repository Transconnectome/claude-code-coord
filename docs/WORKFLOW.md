# Workflow Reference — 6-Stage Pipeline

This document describes each stage of the `/coord` pipeline in detail, including inputs, processing logic, outputs, and the tools involved.

이 문서는 `/coord` 파이프라인의 각 단계를 입력, 처리 로직, 출력, 관련 도구를 포함하여 상세히 설명합니다.

---

## Pipeline Overview (파이프라인 개요)

```
User message
     │
     ▼
 Stage 0: BOOTSTRAP
     │  Complexity score > threshold?
     │  Yes ──────────────────────────►  Enter 6-stage pipeline
     │  No  ──────────────────────────►  Direct native response
     ▼
 Stage 1: MEMORY PRE-CHECK  (parallel / 병렬)
     │  Auto-memory  ‖  Serena  ‖  Graphiti
     ▼
 Stage 2: PLAN
     │  Sequential-thinking MCP → dependency map → parallelization analysis
     ▼
 Stage 3: RESEARCH  (parallel where independent / 독립 작업은 병렬)
     │  Explore agents  ‖  deep-research-agent  ‖  context7  ‖  tavily
     ▼
 Stage 4: EXECUTE
     │  Specialist agents → intermediate lint/test → TodoWrite tracking
     ▼
 Stage 5: REVIEW
     │  critic agent (parallel with generator if Opus model)
     │  Optional: premium model review via OpenRouter
     ▼
 Stage 6: MEMORY UPDATE
     │  Route lessons → Auto-memory > Graphiti > Serena
     │  Update MEMORY.md index
     ▼
   Done
```

---

## Stage 0 — Bootstrap (준비 단계)

**Purpose:** Measure task complexity and decide whether to engage the full pipeline or respond directly.

**목적:** 작업 복잡도를 측정하고 전체 파이프라인을 실행할지 직접 응답할지 결정합니다.

### Input (입력)

- Raw user message text (원시 사용자 메시지 텍스트)
- Active Claude Code session context (활성 Claude Code 세션 컨텍스트)

### Processing (처리)

The bootstrap stage scores the task across four dimensions:

| Dimension (차원) | Signal (신호) | Weight (가중치) |
|-----------------|--------------|----------------|
| Scope ambiguity (범위 모호성) | Vague verbs, qualifiers like "maybe", "explore" | 0.25 |
| Domain count (도메인 수) | Mentions of frontend + backend, infra + code, etc. | 0.30 |
| Step count (단계 수) | Estimated number of sequential operations | 0.25 |
| Risk level (위험 수준) | Production environment, destructive ops, PII | 0.20 |

If the composite score exceeds **0.5**, the full pipeline activates. Below that threshold, Claude responds without the pipeline overhead.

복합 점수가 **0.5**를 초과하면 전체 파이프라인이 활성화됩니다. 그 이하에서는 파이프라인 오버헤드 없이 Claude가 직접 응답합니다.

### Output (출력)

- `mode`: `pipeline` or `direct` (파이프라인 또는 직접)
- `complexity_score`: float 0.0–1.0
- `task_summary`: one-sentence restatement of the request (요청의 한 문장 재진술)

---

## Stage 1 — Memory Pre-Check (메모리 사전 확인)

**Purpose:** Retrieve all relevant prior context before any planning occurs, so the plan does not repeat solved problems.

**목적:** 계획이 발생하기 전에 모든 관련 이전 컨텍스트를 검색하여 계획이 이미 해결된 문제를 반복하지 않도록 합니다.

### Input (입력)

- `task_summary` from Stage 0 (Stage 0의 작업 요약)
- Known project identifiers (알려진 프로젝트 식별자)

### Processing — Parallel scan (병렬 스캔)

All three sources are queried **simultaneously** (세 소스를 **동시에** 조회합니다):

**Source 1: Auto-memory** (`~/.claude/projects/…/memory/`)

```
scan MEMORY.md index
└── read relevant topic files: feedback_*.md, *_project.md, lessons/
```

**Source 2: Serena MCP**

```
list_memories()          → active workspace memory
read_memory("*_plan")   → any existing implementation plans
```

**Source 3: Graphiti** (`graphiti-memory`)

```
search_nodes(query=task_summary)        → related entities
search_memory_facts(query=task_summary) → relationships and decisions
```

> Note: Graphiti requires an OpenRouter embedding API key. If unavailable, this source is skipped gracefully and a warning is logged. (Graphiti는 OpenRouter 임베딩 API 키가 필요합니다. 사용할 수 없는 경우 경고를 기록하고 건너뜁니다.)

### Output (출력)

- `prior_context`: merged dict of all retrieved facts (검색된 모든 사실의 병합 딕셔너리)
- `lessons_loaded`: list of lesson file names that were read (읽은 교훈 파일 이름 목록)
- `existing_plan`: optional, if a plan was found in memory (선택적, 메모리에서 계획이 발견된 경우)

---

## Stage 2 — Plan (계획 단계)

**Purpose:** Produce a structured, dependency-aware execution plan that explicitly identifies which steps can run in parallel.

**목적:** 병렬로 실행할 수 있는 단계를 명시적으로 식별하는 구조화된 의존성 인식 실행 계획을 생성합니다.

### Input (입력)

- `task_summary` (작업 요약)
- `prior_context` from Stage 1 (Stage 1의 이전 컨텍스트)

### Processing (처리)

The `sequential-thinking` MCP is the primary tool for this stage. It performs structured multi-step reasoning with hypothesis testing.

`sequential-thinking` MCP가 이 단계의 기본 도구입니다. 가설 테스트와 함께 구조화된 다단계 추론을 수행합니다.

```
sequential-thinking:
  step 1: Understand the task boundaries (작업 경계 이해)
  step 2: Identify all required subtasks (필요한 모든 하위 작업 식별)
  step 3: Map dependencies between subtasks (하위 작업 간 의존성 매핑)
  step 4: Separate sequential chains from parallel groups (순차 체인과 병렬 그룹 분리)
  step 5: Estimate resource usage and agent types needed (리소스 사용량 및 필요한 에이전트 유형 추정)
  step 6: Output structured plan with parallelization annotations (병렬화 주석과 함께 구조화된 계획 출력)
```

If the task is ambiguous, a `requirements-analyst` subagent clarifies the request before planning continues.

작업이 모호한 경우, `requirements-analyst` 서브에이전트가 계획을 계속하기 전에 요청을 명확히 합니다.

### Parallelization principle (병렬화 원칙)

The plan explicitly marks every task as one of:

계획은 모든 작업을 다음 중 하나로 명시적으로 표시합니다:

- `PARALLEL` — can start at the same time as other PARALLEL tasks (다른 PARALLEL 작업과 동시에 시작 가능)
- `SEQUENTIAL(after=X)` — must wait for task X to complete (작업 X가 완료될 때까지 기다려야 함)
- `BLOCKING` — must complete before any next stage begins (다음 단계가 시작되기 전에 완료되어야 함)

**Why parallelization matters:** Running 3 independent file reads in parallel saves 60–70% of wall-clock time compared to sequential execution. The plan stage forces this analysis upfront so execution does not default to unnecessary serialization.

**병렬화가 중요한 이유:** 3개의 독립적인 파일 읽기를 병렬로 실행하면 순차 실행에 비해 실제 시간의 60-70%를 절약할 수 있습니다.

### Output (출력)

- Structured plan document written to `write_memory("current_plan", …)` (구조화된 계획 문서)
- `TodoWrite` tasks created for all subtasks (모든 하위 작업에 대한 `TodoWrite` 작업 생성)

---

## Stage 3 — Research (리서치 단계)

**Purpose:** Gather all information required for execution before any code is written or files are modified.

**목적:** 코드가 작성되거나 파일이 수정되기 전에 실행에 필요한 모든 정보를 수집합니다.

### Input (입력)

- Plan from Stage 2 (Stage 2의 계획)
- Research tasks identified in the plan (계획에서 식별된 리서치 작업)

### Processing — Parallel agent dispatch (병렬 에이전트 발송)

Multiple research subagents are dispatched simultaneously. Each covers a different domain.

여러 리서치 서브에이전트가 동시에 발송됩니다. 각각 다른 도메인을 담당합니다.

```
Parallel dispatch (병렬 발송):
├── Explore agent(s)         → codebase structure, existing patterns
├── deep-research-agent      → web sources, academic papers, blog posts
└── context7 MCP             → official library documentation

Additional routing:
├── tavily                   → current events, recent releases
└── notebooklm               → long-form document analysis
```

**Research routing rules (리서치 라우팅 규칙):**

| Query type (쿼리 유형) | Route to (라우팅 대상) |
|-----------------------|----------------------|
| "How does X work in the codebase?" | Explore agent |
| "What is the latest version of X?" | Tavily |
| "How does library X handle Y?" | Context7 MCP |
| "Summarize this 50-page PDF" | NotebookLM |
| "Compare three approaches to Z" | deep-research-agent |

### Output (출력)

- `research_findings`: merged summary from all agents (모든 에이전트의 병합 요약)
- Source citations with credibility scores (신뢰도 점수가 있는 소스 인용)

---

## Stage 4 — Execute (실행 단계)

**Purpose:** Implement the plan using specialist agents, with intermediate validation gates.

**목적:** 중간 검증 게이트와 함께 전문가 에이전트를 사용하여 계획을 구현합니다.

### Input (입력)

- Approved plan (승인된 계획)
- Research findings (리서치 결과)
- `TodoWrite` task list (작업 목록)

### Processing (처리)

Tasks are dispatched to specialist agents matching the work type. Agents update `TodoWrite` status as they complete each item.

작업은 작업 유형에 맞는 전문가 에이전트에게 발송됩니다. 에이전트는 각 항목을 완료할 때 `TodoWrite` 상태를 업데이트합니다.

**Agent selection by task type (작업 유형별 에이전트 선택):**

| Task (작업) | Agent (에이전트) |
|------------|----------------|
| API design, server logic | `backend-architect` |
| React components, CSS | `frontend-architect` |
| Data pipelines, scripts | `python-expert` |
| Full system cross-domain | `system-architect` |
| Security audit | `security-engineer` |
| Performance bottleneck | `performance-engineer` |
| Test suite creation | `quality-engineer` |
| Docs and guides | `technical-writer` |
| Code smells, refactor | `refactoring-expert` |

**Intermediate validation (중간 검증):**

After each logical group of changes, the pipeline runs:

각 논리적 변경 그룹 후 파이프라인이 실행합니다:

```bash
# Language-appropriate checks (언어에 따른 검사)
python -m pytest                   # Python projects
npm run lint && npm run typecheck  # JavaScript/TypeScript
go test ./...                      # Go projects
cargo test                         # Rust projects
```

Failures block further execution and trigger a `root-cause-analyst` agent.

실패는 추가 실행을 차단하고 `root-cause-analyst` 에이전트를 트리거합니다.

### Output (출력)

- All planned code changes applied and validated (계획된 모든 코드 변경 적용 및 검증)
- Updated `TodoWrite` with completed statuses (완료 상태가 업데이트된 `TodoWrite`)
- Memory checkpoint: `write_memory("checkpoint_…", current_state)` (메모리 체크포인트)

---

## Stage 5 — Review (리뷰 단계)

**Purpose:** Independent quality check to catch errors, compliance issues, and sycophantic reasoning in the output.

**목적:** 출력에서 오류, 규정 준수 문제, 아첨적 추론을 발견하기 위한 독립적인 품질 검사입니다.

### Input (입력)

- All artifacts produced in Stage 4 (Stage 4에서 생성된 모든 결과물)
- Original plan and requirements (원래 계획 및 요구사항)

### Processing (처리)

**Standard review (표준 리뷰):**

The `critic` agent runs in parallel with the primary generator when an Opus model is used. It applies Popperian falsifiability checks: every claim must include a "wrong if X" condition.

`critic` 에이전트는 Opus 모델 사용 시 기본 생성기와 병렬로 실행됩니다. Popperian 반증 가능성 검사를 적용합니다: 모든 주장에는 "X인 경우 틀림" 조건이 포함되어야 합니다.

**Premium review (프리미엄 리뷰, optional):**

For high-stakes work (proposals, papers, production deployments), a second independent review uses a premium model via OpenRouter:

고위험 작업(제안서, 논문, 프로덕션 배포)의 경우, 두 번째 독립적인 검토가 OpenRouter를 통한 프리미엄 모델을 사용합니다:

```
OpenRouter → Gemini 2.5 Pro  (검토 1)
OpenRouter → GPT-4.1 o3     (검토 2)
```

### Output (출력)

- Review report with pass/fail per criterion (기준별 통과/실패가 있는 검토 보고서)
- Falsifiability score: fraction of claims with `wrong-if-X` conditions (반증 가능성 점수)
- Approval to proceed, or revision requests (진행 승인 또는 수정 요청)

---

## Stage 6 — Memory Update (메모리 업데이트 단계)

**Purpose:** Preserve lessons, decisions, and new knowledge for future sessions.

**목적:** 미래 세션을 위해 교훈, 결정, 새로운 지식을 보존합니다.

### Input (입력)

- Session outcomes (세션 결과)
- Review findings (검토 결과)
- Any errors or surprises encountered (발생한 오류 또는 예상치 못한 상황)

### Memory routing rules (메모리 라우팅 규칙)

| Content type (내용 유형) | Route to (라우팅 대상) | File pattern (파일 패턴) |
|-------------------------|----------------------|------------------------|
| Code locations, symbols (코드 위치, 심볼) | Serena MCP | workspace memory |
| User preferences, lessons (사용자 선호, 교훈) | Auto-memory | `feedback_*.md` |
| Project status (프로젝트 상태) | Auto-memory | `*_project.md` |
| Domain facts, decisions (도메인 사실, 결정) | Graphiti (if running) | knowledge graph node |
| Session summary (세션 요약) | Auto-memory | `*_handoff.md` |

**Priority order (우선순위 순서):** Auto-memory > Graphiti > Serena

### Processing (처리)

```
1. write_memory("session_summary", outcomes)         → Serena
2. Append lesson to feedback_*.md                    → Auto-memory
3. Update MEMORY.md index (one line per entry)       → Auto-memory
4. graphiti: add_memory(episode) for domain facts    → Graphiti (if available)
5. delete_memory("checkpoint_*") for temp items      → Serena
```

### Output (출력)

- Updated persistent memory across all three stores (세 저장소 모두의 업데이트된 영구 메모리)
- MEMORY.md index reflects new entries (MEMORY.md 인덱스가 새 항목을 반영)

---

## Anti-Patterns (피해야 할 패턴)

The following patterns violate the pipeline's design principles and will produce worse outcomes than simply responding directly.

다음 패턴은 파이프라인의 설계 원칙을 위반하며 직접 응답하는 것보다 더 나쁜 결과를 낳습니다.

| Anti-pattern (피해야 할 패턴) | Why it is harmful (해로운 이유) |
|------------------------------|-------------------------------|
| Skipping memory check (메모리 확인 건너뛰기) | Repeats solved problems from previous sessions (이전 세션에서 해결된 문제 반복) |
| Jump-to-implementation (계획 없이 즉시 구현) | Produces code that misses edge cases and requirements (엣지 케이스 및 요구사항을 놓친 코드 생성) |
| Sequential where parallel is possible (병렬 가능 시 순차 실행) | Wastes 60–70% of available execution time (사용 가능한 실행 시간의 60-70% 낭비) |
| Using /coord for simple tasks (단순 작업에 /coord 사용) | Pipeline overhead exceeds task time (파이프라인 오버헤드가 작업 시간 초과) |
| Skipping critic review (critic 검토 건너뛰기) | Sycophantic reasoning goes undetected (아첨적 추론이 감지되지 않음) |
| Omitting memory update (메모리 업데이트 생략) | Lessons are lost and re-learned unnecessarily (교훈이 사라지고 불필요하게 다시 학습) |
| 3+ sequential searches in one context | Delegate to parallel subagents instead (병렬 서브에이전트에 위임) |
