# When to Use /coord (사용 시점 가이드)

This guide helps you decide when the `/coord` 6-stage pipeline adds value versus when it is faster to respond directly without it.

이 가이드는 `/coord` 6단계 파이프라인이 가치를 추가하는 경우와 없이 직접 응답하는 것이 더 빠른 경우를 결정하는 데 도움을 줍니다.

The pipeline has overhead: memory scans, planning, agent coordination. For simple tasks that overhead exceeds the benefit. The examples below give you a clear mental model.

파이프라인에는 오버헤드가 있습니다: 메모리 스캔, 계획, 에이전트 조정. 단순한 작업에서는 그 오버헤드가 이점을 초과합니다.

---

## Use /coord When... (다음 경우에 /coord 사용)

### 1. The task spans multiple files, domains, or services (여러 파일, 도메인, 서비스에 걸친 작업)

Tasks that require changing the backend, database schema, and frontend simultaneously benefit from the planning and coordination stages. Without a plan, changes in one layer often break another.

백엔드, 데이터베이스 스키마, 프론트엔드를 동시에 변경해야 하는 작업은 계획 및 조정 단계에서 이점을 얻습니다.

```
/coord "Add a notification system: backend event bus, database notification table,
        REST endpoint, and React notification bell component"
```

---

### 2. You are unsure how the codebase handles a concern (코드베이스 처리 방식이 불확실한 경우)

When you need to understand existing patterns before writing new code, the Explore agents in Stage 3 find the answers in parallel across all relevant files.

새 코드를 작성하기 전에 기존 패턴을 이해해야 할 때, Stage 3의 Explore 에이전트가 모든 관련 파일에 걸쳐 병렬로 답을 찾습니다.

```
/coord "Add rate limiting to all authenticated endpoints. First, find how
        authentication is currently enforced and where middleware is registered."
```

---

### 3. The task involves a refactor that could have side effects (사이드 이펙트가 있을 수 있는 리팩토링)

Refactoring changes behavior-preserving structure. The pipeline's quality-engineer and critic agents verify correctness before and after, catching regressions early.

리팩토링은 동작을 보존하는 구조를 변경합니다. 파이프라인의 quality-engineer와 critic 에이전트가 이전과 이후에 정확성을 검증하여 회귀를 조기에 발견합니다.

```
/coord "Refactor the UserService God class (800 lines) into AuthService,
        ProfileService, and SessionService without changing behavior"
```

---

### 4. You are making an architectural decision with long-term consequences (장기적 결과가 있는 아키텍처 결정)

Architecture decisions are expensive to reverse. The planning stage applies the `system-architect` agent with `sequential-thinking` to model trade-offs before any code is written.

아키텍처 결정은 되돌리기 비용이 큽니다. 계획 단계는 코드가 작성되기 전에 트레이드오프를 모델링하기 위해 `sequential-thinking`과 함께 `system-architect` 에이전트를 적용합니다.

```
/coord "Decide whether to use Postgres with row-level security or
        separate schemas for multi-tenancy in our SaaS product.
        We have 50 tenants now and expect 2,000 in 18 months."
```

---

### 5. The task requires real-time web research (실시간 웹 리서치가 필요한 경우)

If solving the problem requires current information (library releases post-2024, recent CVEs, breaking API changes), the pipeline routes to `deep-research-agent` and `tavily` automatically.

문제 해결에 최신 정보가 필요한 경우, 파이프라인이 자동으로 `deep-research-agent`와 `tavily`로 라우팅합니다.

```
/coord "Upgrade the project from React 17 to React 19.
        Identify all breaking changes, codemods available, and
        third-party library compatibility issues."
```

---

### 6. You need independent review of your own output (자신의 출력에 대한 독립적 검토 필요)

When the risk of a wrong decision is high, the critic agent in Stage 5 provides a falsifiability-checked review that is independent of the generator's reasoning.

잘못된 결정의 위험이 높을 때, Stage 5의 critic 에이전트는 생성기의 추론과 독립된 반증 가능성 확인 검토를 제공합니다.

```
/coord "Review the disaster recovery plan I've written for the production
        PostgreSQL cluster. Challenge every assumption."
```

---

### 7. The task will take multiple sessions to complete (여러 세션에 걸쳐 완료되는 작업)

The pipeline's memory update in Stage 6 stores the plan, progress, and lessons. When you resume the next day, Stage 1 retrieves this context and the plan stage finds the existing checkpoint.

파이프라인의 Stage 6 메모리 업데이트가 계획, 진행 상황, 교훈을 저장합니다. 다음 날 재개할 때 Stage 1이 이 컨텍스트를 검색합니다.

```
/coord "Implement the full OAuth 2.0 flow with Google and GitHub.
        This will take multiple sessions. Track progress."
```

---

### 8. You suspect there are lessons from past sessions relevant to this task (과거 세션의 관련 교훈이 있을 가능성)

The memory pre-check in Stage 1 surfaces lessons from `feedback_*.md` files and pattern libraries that are relevant to the current task, preventing repeated mistakes.

Stage 1의 메모리 사전 확인이 현재 작업과 관련된 `feedback_*.md` 파일과 패턴 라이브러리에서 교훈을 표면화하여 반복 실수를 방지합니다.

```
/coord "Set up the CI/CD pipeline for the new service"
# Stage 1 will surface: any prior CI lessons, known pitfalls from past deployments
```

---

### 9. The task is a debugging investigation with unclear root cause (근본 원인이 불분명한 디버깅 조사)

Unexplained failures benefit from the `sci-method` or `root-cause-analyst` agents, which apply systematic hypothesis generation and decisive experiment design.

설명되지 않는 실패는 체계적인 가설 생성과 결정적 실험 설계를 적용하는 `sci-method` 또는 `root-cause-analyst` 에이전트에서 이점을 얻습니다.

```
/coord "Our ML model achieves 95% AUC in validation but 61% on test data.
        This started after we updated the data pipeline last Tuesday."
```

---

### 10. User pressure may be pushing toward a bad decision (사용자 압력이 나쁜 결정을 유발할 가능성)

The anti-sycophancy hooks fire on scope-change and personnel-change directives. When you feel uncertain whether to push back, `/coord` provides structured cost-of-compliance analysis before acting.

훅이 범위 변경 및 인사 변경 지시에 실행됩니다. 반대해야 할지 불확실할 때 `/coord`는 행동 전에 구조화된 준수 비용 분석을 제공합니다.

```
/coord "The PI wants to pivot the entire paper from Method A to Method B
        after three reviewers gave mixed signals. Evaluate whether to comply."
```

---

## Do NOT Use /coord When... (/coord를 사용하지 말아야 할 경우)

### 1. The task is a simple single-file edit (단순 단일 파일 편집)

```
# Just do this directly (직접 수행):
"Fix the typo in line 42 of utils.py"
"Change the button color to #0070f3"
"Add a comment explaining this function"
```

The pipeline adds 30–60 seconds of overhead that exceeds the time to make the edit directly. (파이프라인은 직접 편집하는 시간을 초과하는 30-60초의 오버헤드를 추가합니다.)

---

### 2. The answer is a factual question (사실적 질문)

```
# Just ask directly (직접 질문):
"What is the default timeout in httpx?"
"What does the @classmethod decorator do?"
"What is the difference between == and is in Python?"
```

These questions do not benefit from memory scanning, planning, or agent coordination. (이러한 질문은 메모리 스캔, 계획 또는 에이전트 조정에서 이점을 얻지 못합니다.)

---

### 3. You need a quick code snippet (빠른 코드 스니펫 필요)

```
# Just ask directly (직접 요청):
"Write a Python one-liner to filter even numbers from a list"
"Show me how to parse a URL in JavaScript"
```

---

### 4. The task is casual conversation (일상적인 대화)

```
# Not suitable for /coord (적합하지 않음):
"What do you think about this approach?"
"Can you explain this concept again?"
"Thanks, that worked!"
```

---

### 5. Time is critically short (시간이 극히 부족한 경우)

If you need an answer in under 10 seconds, skip the pipeline. The planning and memory stages add latency that is only worthwhile for tasks with real complexity.

10초 이내에 답변이 필요한 경우 파이프라인을 건너뛰세요. 계획 및 메모리 단계는 실제 복잡성이 있는 작업에만 가치 있는 지연을 추가합니다.

---

## Real Scenarios with Code Examples (코드 예시가 있는 실제 시나리오)

### Scenario 1: Adding user permissions to a multi-service application (다중 서비스 애플리케이션에 사용자 권한 추가)

```
/coord "Add role-based access control to the application. Users can be
        'viewer', 'editor', or 'admin'. This affects the FastAPI backend
        (endpoint decorators), PostgreSQL (permissions table), and
        the React dashboard (hide edit buttons for viewers)."
```

**What /coord does (수행 내용):**
- Stage 1: Checks memory for prior auth lessons (사전 인증 교훈 확인)
- Stage 2: Plans 9 subtasks with dependency map (9개 하위 작업 계획)
- Stage 3: Explore finds existing auth patterns; context7 retrieves FastAPI security docs (기존 인증 패턴 탐색)
- Stage 4: `backend-architect` handles API + DB, `frontend-architect` handles React (전문가 에이전트 분담)
- Stage 5: `security-engineer` reviews the permission logic (보안 검토)
- Stage 6: Saves RBAC patterns to memory (패턴 메모리 저장)

---

### Scenario 2: Performance investigation (성능 조사)

```
/coord "The /api/reports endpoint takes 12 seconds. Before the last
        deploy it took 0.8 seconds. Investigate and fix."
```

**What /coord does (수행 내용):**
- Stage 1: Retrieves any prior performance lessons (사전 성능 교훈 검색)
- Stage 2: Plans investigation → hypothesis generation → fix → verify (조사 계획)
- Stage 3: Explore agent reads git diff from last deploy; `root-cause-analyst` generates hypotheses (원인 가설 생성)
- Stage 4: `performance-engineer` profiles and implements fix (성능 수정 구현)
- Stage 5: Verifies improvement with benchmark (벤치마크로 개선 검증)

---

### Scenario 3: Proposal review with push-back check (반대 의견 확인이 포함된 제안서 검토)

```
/coord "The team wants to abandon the current microservices architecture
        and rewrite as a monolith. Evaluate whether to comply."
```

**What /coord does (수행 내용):**
- Hook: `chavis_strategic_challenge.py` generates Strategic Challenge Template (전략 도전 템플릿 생성)
- Stage 2: `system-architect` models costs of both architectures (두 아키텍처 비용 모델링)
- Stage 3: `deep-research-agent` researches monolith-vs-microservices trade-offs (트레이드오프 리서치)
- Stage 5: `critic` challenges the recommendation (권장 사항 도전)
- Output: Structured recommendation with cost-of-compliance analysis (준수 비용 분석 포함 권장 사항)

---

### Scenario 4: Multi-session implementation (다중 세션 구현)

```
# Session 1
/coord "Begin implementing the ML model serving pipeline.
        We need: model registry, REST inference endpoint, async batch processing,
        and monitoring. Track progress across sessions."

# Session 2 (next day) — pipeline finds the existing plan in memory
/coord "Continue the ML serving pipeline implementation. Where did we leave off?"
```

**What /coord does across sessions (세션 간 수행 내용):**
- Session 1, Stage 6: Writes plan + progress to Serena and auto-memory (진행 상황 저장)
- Session 2, Stage 1: Retrieves plan, identifies completed vs pending tasks (기존 계획 검색)
- Session 2, Stage 2: Resumes from checkpoint (체크포인트에서 재개)

---

### Scenario 5: Scientific anomaly diagnosis (과학적 이상 진단)

```
/coord "Our fMRI preprocessing pipeline produces different connectivity matrices
        depending on whether it runs on Linux or macOS, even with identical inputs.
        This is blocking paper submission. Diagnose and fix."
```

**What /coord does (수행 내용):**
- Stage 2: `sci-method` generates ranked hypotheses (가설 생성)
- Stage 3: Explore searches for floating-point or OS-dependent code paths (OS 의존 코드 경로 탐색)
- Stage 3: `deep-research-agent` searches for known numerical reproducibility issues in neuroimaging libraries (알려진 수치 재현성 문제 검색)
- Stage 4: `python-expert` implements reproducibility fixes (재현성 수정 구현)
- Stage 5: `quality-engineer` writes regression tests (회귀 테스트 작성)
