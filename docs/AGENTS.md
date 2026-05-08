# Specialist Agents Reference (전문가 에이전트 참조)

This document lists every specialist agent available in the `/coord` pipeline, with its role, activation condition, `subagent_type` value, and a concrete invocation example.

이 문서는 `/coord` 파이프라인에서 사용 가능한 모든 전문가 에이전트를 역할, 활성화 조건, `subagent_type` 값, 구체적인 호출 예시와 함께 나열합니다.

---

## How Agents Are Invoked (에이전트 호출 방법)

Agents are dispatched using Claude Code's `subagent_type` parameter, either by the pipeline automatically or by the user directly via the `@sub` shorthand.

에이전트는 파이프라인이 자동으로 또는 사용자가 `@sub` 단축어를 통해 직접 `subagent_type` 매개변수를 사용하여 발송됩니다.

```python
# Internal pipeline dispatch (파이프라인 내부 발송)
{
  "subagent_type": "explore",
  "prompt": "Find all authentication-related files in the repository",
  "run_in_background": True
}

# User shorthand (사용자 단축어)
@sub Find all authentication-related files in the repository
```

The pipeline selects the right agent automatically based on task classification from Stage 2. Manual `@sub` invocations bypass the pipeline and run the agent directly.

파이프라인은 Stage 2의 작업 분류를 기반으로 자동으로 올바른 에이전트를 선택합니다. 수동 `@sub` 호출은 파이프라인을 우회하고 에이전트를 직접 실행합니다.

---

## Discovery and Exploration Agents (탐색 에이전트)

### `explore`

**Role:** Codebase discovery, file structure mapping, and pattern identification. Use when the task requires understanding what already exists before making changes.

**역할:** 코드베이스 탐색, 파일 구조 매핑, 패턴 식별. 변경하기 전에 무엇이 존재하는지 이해해야 할 때 사용합니다.

**When to use (사용 시점):**
- Any task involving 3 or more search queries (3개 이상의 검색 쿼리가 포함된 모든 작업)
- "How is X implemented in this codebase?" questions (코드베이스에서 X가 어떻게 구현되는지 질문)
- Before refactoring to understand current architecture (현재 아키텍처를 이해하기 위해 리팩토링 전)

**Example (예시):**
```
@sub Find all places in the codebase where database connections are opened,
     and check whether they are properly closed in finally blocks.
```

---

### `deep-research-agent`

**Role:** Multi-source web research, synthesis across academic papers, blog posts, and official documentation. Returns a structured report with citations.

**역할:** 다중 소스 웹 리서치, 학술 논문, 블로그 포스트, 공식 문서 간 합성. 인용과 함께 구조화된 보고서를 반환합니다.

**When to use (사용 시점):**
- Comparing approaches to solve a technical problem (기술적 문제 해결 접근법 비교)
- Finding recent (post-knowledge-cutoff) information (지식 컷오프 이후 최신 정보 찾기)
- Literature survey for a research paper or proposal (논문 또는 제안서를 위한 문헌 조사)

**Example (예시):**
```
@sub Research the current state of transformer model compression techniques
     for edge deployment. Compare pruning, quantization, and distillation
     approaches. Include papers from 2024 onward.
```

---

## Planning Agents (계획 에이전트)

### `plan`

**Role:** Implementation strategy design. Produces a structured plan with dependency mapping, parallelization annotations, and resource estimates. Should run before any implementation work begins.

**역할:** 구현 전략 설계. 의존성 매핑, 병렬화 주석, 리소스 추정이 있는 구조화된 계획을 생성합니다. 구현 작업이 시작되기 전에 실행해야 합니다.

**When to use (사용 시점):**
- Before implementing any feature with 3+ steps (3단계 이상의 기능 구현 전)
- When requirements are clear but the execution order is not (요구사항은 명확하지만 실행 순서가 불명확할 때)

**Example (예시):**
```
@sub Design an implementation plan for adding rate limiting to the FastAPI
     service. The plan must identify which components need changes, the order
     of changes, and which steps can be parallelized.
```

---

### `requirements-analyst`

**Role:** Ambiguous request clarification. Converts vague user intents into precise, numbered requirements with acceptance criteria. Prevents scope creep by surfacing implicit assumptions.

**역할:** 모호한 요청 명세화. 모호한 사용자 의도를 수용 기준이 있는 정확한 번호 매겨진 요구사항으로 변환합니다.

**When to use (사용 시점):**
- When the user's request has multiple valid interpretations (사용자 요청에 여러 유효한 해석이 있을 때)
- Before starting any project where the scope is unclear (범위가 불명확한 프로젝트 시작 전)

**Example (예시):**
```
@sub Clarify this requirement: "Make the dashboard faster."
     Identify: which dashboard, which metrics define "faster",
     what the current baseline is, and what success looks like.
```

---

## Architecture Agents (아키텍처 에이전트)

### `system-architect`

**Role:** Full-system cross-domain design. Produces architecture diagrams (ASCII), component responsibility assignments, data flow descriptions, and integration contracts.

**역할:** 전체 시스템 도메인 간 설계. ASCII 아키텍처 다이어그램, 컴포넌트 책임 할당, 데이터 흐름 설명, 통합 계약을 생성합니다.

**When to use (사용 시점):**
- Designing a new system from scratch (새 시스템 처음부터 설계)
- Evaluating a proposed architecture change (제안된 아키텍처 변경 평가)
- Cross-cutting concerns spanning frontend + backend + infra (프론트엔드 + 백엔드 + 인프라에 걸친 횡단 관심사)

**Example (예시):**
```
@sub Design the architecture for a real-time collaborative document editor.
     Include the WebSocket layer, CRDT conflict resolution approach,
     persistence strategy, and how the frontend state synchronizes.
```

---

### `backend-architect`

**Role:** Server-side system design. Specializes in API design, database schema, service decomposition, authentication flows, and caching strategies.

**역할:** 서버 사이드 시스템 설계. API 설계, 데이터베이스 스키마, 서비스 분해, 인증 흐름, 캐싱 전략을 전문으로 합니다.

**When to use (사용 시점):**
- Designing REST or GraphQL APIs (REST 또는 GraphQL API 설계)
- Planning database schema migrations (데이터베이스 스키마 마이그레이션 계획)
- Service decomposition from monolith (모놀리스에서 서비스 분해)

**Example (예시):**
```
@sub Design the database schema for a multi-tenant SaaS application where
     each tenant has isolated data. Choose between row-level security,
     schema-per-tenant, and database-per-tenant, and justify the choice.
```

---

### `frontend-architect`

**Role:** UI/UX architecture decisions. Handles state management strategy, component hierarchy, routing architecture, rendering strategy (SSR/CSR/SSG), and accessibility compliance.

**역할:** UI/UX 아키텍처 결정. 상태 관리 전략, 컴포넌트 계층, 라우팅 아키텍처, 렌더링 전략(SSR/CSR/SSG), 접근성 규정 준수를 처리합니다.

**When to use (사용 시점):**
- Choosing a React state management library (React 상태 관리 라이브러리 선택)
- Designing component composition patterns (컴포넌트 합성 패턴 설계)
- Performance optimization for a large SPA (대규모 SPA 성능 최적화)

**Example (예시):**
```
@sub Evaluate whether to use Zustand, Jotai, or Redux Toolkit for
     the state management layer in a Next.js 14 app with server components.
     Consider the server/client boundary implications.
```

---

## Implementation Agents (구현 에이전트)

### `python-expert`

**Role:** Python-specific implementation. Handles async patterns, type hinting, packaging, testing with pytest, and Python performance patterns.

**역할:** Python 특화 구현. 비동기 패턴, 타입 힌팅, 패키징, pytest를 사용한 테스트, Python 성능 패턴을 처리합니다.

**When to use (사용 시점):**
- Writing Python code that must follow strict typing conventions (엄격한 타이핑 규칙을 따라야 하는 Python 코드 작성)
- Async FastAPI or Django endpoints (비동기 FastAPI 또는 Django 엔드포인트)
- Scientific computing with NumPy, pandas, or PyTorch (NumPy, pandas, PyTorch를 사용한 과학 계산)

**Example (예시):**
```
@sub Implement an async context manager in Python 3.12 that manages
     a connection pool for PostgreSQL using asyncpg. Include type hints,
     docstrings, and a pytest fixture that uses the manager.
```

---

### `refactoring-expert`

**Role:** Code quality improvement without behavior changes. Identifies dead code, extracts functions, removes duplication, applies SOLID principles, and improves naming.

**역할:** 동작 변경 없는 코드 품질 개선. 데드 코드 식별, 함수 추출, 중복 제거, SOLID 원칙 적용, 이름 개선을 수행합니다.

**When to use (사용 시점):**
- When code works but is difficult to maintain (코드는 작동하지만 유지 관리가 어려울 때)
- Before adding new features to legacy code (레거시 코드에 새 기능을 추가하기 전)
- Code review cleanup (코드 리뷰 정리)

**Example (예시):**
```
@sub Refactor the authentication module in src/auth/. It currently has a
     500-line God class. Extract the token validation, session management,
     and OAuth flow into separate classes. Do not change behavior.
```

---

## Quality and Safety Agents (품질 및 안전 에이전트)

### `critic`

**Role:** Independent review with falsifiability checking. Every claim in the reviewed output must have a "wrong if X" condition. Raises compliance issues, logical gaps, and sycophantic reasoning.

**역할:** 반증 가능성 검사와 함께 독립적인 검토. 검토된 출력의 모든 주장에는 "X인 경우 틀림" 조건이 있어야 합니다.

**When to use (사용 시점):**
- Automatically after Stage 4 when Opus model is used (Opus 모델 사용 시 Stage 4 후 자동)
- Manually via `/challenge` command to critique the last response (마지막 응답을 비판하기 위해 `/challenge` 명령으로 수동)
- Before finalizing any proposal, paper, or production deployment (제안서, 논문, 프로덕션 배포 확정 전)

**Example (예시):**
```
@sub Review the proposed caching strategy below and identify:
     1. Any claims without evidence
     2. Edge cases not handled
     3. Performance assumptions that could be wrong
     [paste the caching strategy]
```

---

### `quality-engineer`

**Role:** Test suite design and coverage analysis. Creates unit tests, integration tests, and property-based tests. Identifies uncovered code paths and writes assertions with meaningful failure messages.

**역할:** 테스트 스위트 설계 및 커버리지 분석. 단위 테스트, 통합 테스트, 속성 기반 테스트를 생성합니다.

**When to use (사용 시점):**
- After implementing a new feature (새 기능 구현 후)
- When test coverage drops below the project threshold (테스트 커버리지가 프로젝트 임계값 아래로 떨어질 때)
- Property-based testing for data transformation functions (데이터 변환 함수의 속성 기반 테스트)

**Example (예시):**
```
@sub Write a comprehensive pytest test suite for the payment processing module
     in src/payments/. Cover: successful transactions, card decline scenarios,
     network timeout handling, and idempotency of repeated calls.
```

---

### `security-engineer`

**Role:** Threat modeling and vulnerability review. Applies OWASP Top 10, checks for injection vulnerabilities, reviews authentication and authorization logic, and assesses data exposure risks.

**역할:** 위협 모델링 및 취약점 검토. OWASP Top 10 적용, 인젝션 취약점 확인, 인증 및 권한 부여 로직 검토, 데이터 노출 위험 평가를 수행합니다.

**When to use (사용 시점):**
- Before deploying any user-facing authentication feature (사용자 대면 인증 기능 배포 전)
- When handling personally identifiable information (개인 식별 정보 처리 시)
- Annual security audit of a service (서비스의 연간 보안 감사)

**Example (예시):**
```
@sub Perform a security review of the user registration and login flows
     in src/auth/. Check for: SQL injection, timing attacks on password
     comparison, missing rate limiting, and insecure password storage.
```

---

### `performance-engineer`

**Role:** Profiling and optimization. Identifies algorithmic complexity issues, database N+1 queries, memory leaks, and unnecessary network round trips. Provides before/after benchmarks.

**역할:** 프로파일링 및 최적화. 알고리즘 복잡도 문제, 데이터베이스 N+1 쿼리, 메모리 누수, 불필요한 네트워크 라운드 트립을 식별합니다.

**When to use (사용 시점):**
- When profiling shows a hot path (프로파일링이 핫 패스를 표시할 때)
- Unexplained latency increase after a deployment (배포 후 설명되지 않는 지연 증가)
- Scaling review before a traffic spike (트래픽 급증 전 확장성 검토)

**Example (예시):**
```
@sub Analyze the performance of the report generation endpoint. It currently
     takes 8 seconds for a report covering 10,000 rows. Identify the
     bottleneck and propose a fix with estimated improvement.
```

---

## Documentation Agent (문서화 에이전트)

### `technical-writer`

**Role:** Documentation creation and improvement. Writes API references, user guides, architecture docs, README files, and inline code comments. Focuses on clarity for the target audience and WCAG-compliant structure.

**역할:** 문서 생성 및 개선. API 참조, 사용자 가이드, 아키텍처 문서, README 파일, 인라인 코드 주석을 작성합니다.

**When to use (사용 시점):**
- After implementing a new public API (새 공개 API 구현 후)
- Onboarding documentation for a new team member (새 팀원을 위한 온보딩 문서)
- When existing docs are outdated or missing examples (기존 문서가 오래되었거나 예시가 없을 때)

**Example (예시):**
```
@sub Write API reference documentation for the /payments endpoint.
     Audience: external developers integrating for the first time.
     Include: request format, all response codes, error object schema,
     and a working cURL example for each scenario.
```

---

## Scientific and Diagnostic Agents (과학적 및 진단 에이전트)

### `sci-method`

**Role:** Scientific hypothesis-evidence-validation workflow using Cynefin triage, Popperian falsifiability, and Bayesian updating. An 8-stage structured reasoning process for any complex problem domain.

**역할:** Cynefin 분류, Popperian 반증 가능성, Bayesian 업데이트를 사용하는 과학적 가설-증거-검증 워크플로우. 모든 복잡한 문제 도메인을 위한 8단계 구조화된 추론 과정입니다.

**When to use (사용 시점):**
- Diagnosing a system behavior that is not understood (이해되지 않는 시스템 동작 진단)
- Evaluating competing explanations for an experimental result (실험 결과에 대한 경쟁적 설명 평가)
- Any problem where intuition alone is insufficient (직관만으로는 불충분한 모든 문제)

**8-stage workflow (8단계 워크플로우):**

1. Cynefin domain classification (Cynefin 도메인 분류)
2. Phenomenon description (현상 설명)
3. Hypothesis generation (가설 생성)
4. Evidence inventory (증거 목록)
5. Bayesian likelihood scoring (Bayesian 가능성 점수 매기기)
6. Decisive experiment design (결정적 실험 설계)
7. Prediction registration (예측 등록)
8. Update and conclusion (업데이트 및 결론)

**Example (예시):**
```
@sub Apply sci-method to this anomaly: our model achieves 95% AUC on the
     validation set but only 61% on the held-out test set. Generate ranked
     hypotheses with testable predictions for each.
```

---

### `root-cause-analyst`

**Role:** Systematic failure investigation. Applies the "five whys" method combined with evidence gathering. Distinguishes root causes from symptoms. Produces a causal chain diagram.

**역할:** 체계적인 실패 조사. 증거 수집과 결합된 "5 Why" 방법을 적용합니다. 근본 원인과 증상을 구분합니다.

**When to use (사용 시점):**
- After a production incident (프로덕션 인시던트 후)
- When intermediate validation in Stage 4 fails (Stage 4의 중간 검증이 실패할 때)
- Recurring bugs that have been fixed and returned (수정되었다가 다시 발생하는 버그)

**Example (예시):**
```
@sub The CI pipeline has been failing intermittently for 2 weeks.
     Failures occur in the integration test step, always between 02:00–04:00 UTC.
     Apply root cause analysis: gather evidence, generate hypotheses, and
     recommend the decisive diagnostic step.
```

---

## Agent Selection Quick Reference (에이전트 선택 빠른 참조)

| I need to… (할 작업) | Use this agent (사용할 에이전트) |
|---------------------|---------------------------------|
| Find existing code patterns | `explore` |
| Research a technical topic online | `deep-research-agent` |
| Plan implementation before coding | `plan` |
| Clarify vague requirements | `requirements-analyst` |
| Design a full system | `system-architect` |
| Design server APIs and schemas | `backend-architect` |
| Design UI components and state | `frontend-architect` |
| Write Python code | `python-expert` |
| Improve code quality without behavior change | `refactoring-expert` |
| Independently review output for errors | `critic` |
| Write or improve tests | `quality-engineer` |
| Check for security vulnerabilities | `security-engineer` |
| Find and fix performance bottlenecks | `performance-engineer` |
| Write documentation or guides | `technical-writer` |
| Investigate a complex anomaly scientifically | `sci-method` |
| Find the root cause of a failure | `root-cause-analyst` |
