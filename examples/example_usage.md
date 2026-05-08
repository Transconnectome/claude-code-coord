# /coord Usage Examples

Real-world examples of using the `/coord` Intelligent Complex Task Workflow.
(실제 사용 예시 모음)

---

## ✅ When to Use /coord

Use `/coord` when your task has **3+ steps**, **multi-domain scope**, or **unclear requirements**.

---

## 10 Example Scenarios

### 1. Debugging a Multi-Component Failure

```
/coord "Our FastAPI server is returning 500 errors only when Redis is under load.
Debug and fix the race condition."
```

**What happens:**
- Memory Pre-Check: loads past debugging lessons
- Plan: identifies affected components (FastAPI → Redis → connection pool)
- Research: parallel exploration of `api/`, `cache/`, `tests/`
- Execute: `backend-architect` + `root-cause-analyst` agents in parallel
- Review: `critic` validates the fix

---

### 2. Architecting a New Feature

```
/coord "Design and implement a real-time notification system for our app.
Users need push notifications when their experiment finishes."
```

**What happens:**
- Memory Pre-Check: loads project tech stack context
- Plan: `requirements-analyst` clarifies scope, `system-architect` designs
- Research: `context7` fetches WebSocket/SSE docs
- Execute: `frontend-architect` + `backend-architect` parallel implementation
- Review: `quality-engineer` + `security-engineer`

---

### 3. Migrating a Codebase

```
/coord "Migrate our data loading pipeline from Pandas to Polars.
Keep API compatibility. ~30 files affected."
```

**What happens:**
- Memory Pre-Check: previous migration lessons
- Plan: `refactoring-expert` designs migration strategy
- Research: `context7` fetches Polars API docs
- Execute: `morphllm` MCP for bulk pattern-based edits
- Review: `quality-engineer` runs regression tests

---

### 4. Complex Debugging (Unknown Cause)

```
/coord "Our ML model performance dropped 15% after last week's merge.
Find the cause — we don't know which change caused it."
```

**What happens:**
- Memory Pre-Check: prior performance debugging lessons
- Sequential Thinking: systematic hypothesis generation
- Research: `Explore` agents in 3 areas (data, model, training loop)
- Execute: `performance-engineer` + `root-cause-analyst`

---

### 5. Security Audit

```
/coord "Audit our authentication system for OWASP Top 10 vulnerabilities.
Generate a report with severity levels."
```

**What happens:**
- Plan: `security-engineer` designs audit strategy
- Research: parallel file analysis (auth flows, middleware, DB queries)
- Execute: systematic vulnerability scan
- Review: `critic` challenges findings

---

### 6. Writing a Technical Document

```
/coord "Write a comprehensive architecture document for our microservices system.
Target audience: new engineers joining the team."
```

**What happens:**
- Memory Pre-Check: existing architecture notes
- Research: codebase exploration for current system state
- Execute: `technical-writer` agent drafts
- Review: `critic` checks completeness

---

### 7. Planning a Large Refactoring

```
/coord "Refactor our 5,000-line monolithic UserService into separate domain services.
Need a phased migration plan with zero downtime."
```

**What happens:**
- Plan: `requirements-analyst` → `system-architect` design
- Sequential Thinking: dependency mapping, phase breakdown
- Execute: migration plan with rollback points
- Review: risk assessment

---

### 8. Research + Implementation

```
/coord "Research the best Python async job queue for our use case
(100k jobs/day, PostgreSQL backend) and implement it."
```

**What happens:**
- Research: `deep-research-agent` + `tavily` web search
- Plan: technology selection decision
- Execute: implementation with `python-expert`
- Review: `quality-engineer`

---

### 9. Code Review & Quality Improvement

```
/coord "Review our payment processing module for correctness, security,
and performance. Fix all identified issues."
```

**What happens:**
- Research: 3 parallel `Explore` agents (payment flows, error handling, tests)
- Execute: `security-engineer` + `quality-engineer` + `refactoring-expert`
- Review: `critic` validates changes

---

### 10. Multi-Domain Integration

```
/coord "Connect our Python ML pipeline to a React frontend with real-time results.
Include WebSocket connection, progress bar, and error handling."
```

**What happens:**
- Plan: full-stack architecture design
- Execute: `python-expert` (backend) + `frontend-architect` (React) in PARALLEL
- Review: integration testing with `playwright` MCP

---

## ❌ When NOT to Use /coord

```bash
# Too simple — just ask directly
"What is the syntax for Python list comprehensions?"
"Fix this typo in README.md"
"What does this function return?"

# Single clear task
"Add a logging statement to auth.py line 45"
"Run the test suite"
```

---

## Auto-Activation Keywords

When you include these in any prompt, `/coord` activates automatically:

| Korean 한국어 | English |
|--------------|---------|
| 복잡한 작업 | complex task |
| 종합 분석 | comprehensive analysis |
| 시스템 설계 | system design |
| 아키텍처 | architecture |
| 마이그레이션 | migration |
| 리팩터링 계획 | refactoring plan |
| 워크플로우 | workflow |

---

## Memory Routing Examples

After each `/coord` run, context is saved:

```
Code structure/files → Serena MCP
Domain facts (experiments, decisions, meetings) → Graphiti
User preferences/lessons learned → Auto-memory (~/.claude/projects/.../memory/)
```
