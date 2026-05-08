복잡한 작업을 위한 Intelligent Complex Task Workflow 활성화. Memory + Sequential + Plan + Specialist Agents + Critic 파이프라인을 한 번에 가동.

## 사용 시점

**활성화 권장**:
- 구현/설계/디버깅/리팩터링/마이그레이션 작업
- 3+ 단계 또는 multi-domain 문제
- Scope 모호 ("어떻게 해야 할지", "통합", "추가")
- 의사결정 (전략, 아키텍처, 도구 선택)

**활성화 회피**:
- 단순 fact lookup ("X 문법은?")
- Single-file edit / typo fix
- 명확한 단일 작업

## 사용자 요청

$ARGUMENTS

(인자 없을 시 → "어떤 작업을 진행하시겠습니까?" 한 번 묻고 진행)

---

## 표준 워크플로우 (이 명령 호출 시 즉시 실행)

이 워크플로우는 사용자 요청 ($ARGUMENTS) 에 대해 6단계를 **자동 또는 반자동**으로 진행합니다.
각 단계마다 진행 상황을 사용자에게 명시적으로 보고하세요.

### 단계 0: 사전 도구 로드 (Bootstrap)

**병렬 ToolSearch 호출**로 핵심 MCP 도구 로드:

```
ToolSearch(query="select:mcp__graphiti-memory__search_nodes,mcp__graphiti-memory__search_memory_facts,mcp__graphiti-memory__add_memory")
ToolSearch(query="sequential-thinking", max_results=3)
```

Serena 도구는 이미 native 등록되어 있으므로 별도 로드 불필요 (필요 시 ToolSearch로 확인).

코드 편집/리팩터링/마이그레이션 작업 감지 시 추가 로드:
```
ToolSearch(query="select:mcp__morph-mcp__edit_file,mcp__morph-mcp__codebase_search")
```

### 단계 1: Memory Pre-Check (병렬 3-source)

**반드시 병렬 호출**:

1. **Auto-memory 스캔** (Bash):
   ```bash
   bash /home/juke/.claude/skills/coord/memory_scan.sh "$ARGUMENTS"
   ```
   → 작업 키워드와 매칭되는 MEMORY.md 항목 추출

2. **Serena list_memories** — 워크스페이스 컨텍스트 확인 (활성 프로젝트 있을 시)

3. **Graphiti search_nodes** — 도메인 사실 검색 (가능 시; 401 이슈 있으면 skip)
   ```
   mcp__graphiti-memory__search_nodes(query="<task keywords>", max_nodes=5)
   ```

**보고 형식**:
```
## 🧠 Memory Pre-Check
- Auto-memory: <매칭된 lessons/feedback 파일 N개>
- Serena: <세션 메모리 N개>
- Graphiti: <related nodes N개 또는 "skip: embedder 이슈">

관련 컨텍스트:
- [핵심 발견 1]
- [핵심 발견 2]
```

### 단계 2: Plan Phase (작업 분해 + 병렬화 분석)

**도구 위임**:

1. **sequential-thinking MCP** 호출 — 문제 분해 (3-7 thoughts):
   ```
   mcp__sequential-thinking__sequentialthinking(
     thought="작업 분해 시작: <task summary>. 핵심 sub-problem 식별...",
     totalThoughts=5
   )
   ```

2. **Plan agent** launch (Task tool, `subagent_type="Plan"` 또는 fallback `general-purpose`):
   - 입력: 사용자 요청 + Memory 결과
   - 출력: Phase 분해 + 병렬화 가능 단계 + 도메인 specialist 추천

3. **requirements-analyst** (모호 시에만): scope 명확화

**TodoWrite 자동 생성**: Plan 결과 → 3-7개 todo 항목 (Phase 단위)

**보고 형식**:
```
## 📋 Plan
**Phases**:
1. [Phase 1] (Sequential / Parallel: <도구 N개>)
2. [Phase 2] ...

**Specialist Agents 추천**:
- <agent-name>: <역할>

**병렬화 게인**: <X% 시간 단축 예상>
```

### 단계 3: Research Phase (3+ 병렬 위임)

**필요 시에만 활성화** (작업이 정보 수집 필요할 때).
다음 도구를 **병렬**로 launch:

- **Explore agents 3+** (서로 다른 영역, e.g., `tests/`, `src/`, `docs/`)
- **deep-research-agent** (외부 정보 필요 시)
- **WebSearch 또는 Tavily** (보조 검증)
- **context7** (라이브러리 공식 문서)

**보고**:
```
## 🔍 Research
- Explore N agents: <영역 요약>
- 외부 조사: <key findings>
```

### 단계 4: Execute Phase (Specialist 병렬 + 중간 검증)

**도메인별 specialist 병렬 호출** (Plan 단계에서 추천된 agent):

- 코드 작성: `backend-architect` / `frontend-architect` / `python-expert`
- 품질: `quality-engineer` / `refactoring-expert`
- 보안: `security-engineer`
- 성능: `performance-engineer`
- 문서: `technical-writer`

**코드 편집 전략** (agent에게 전달할 결정 기준):

| 편집 유형 | 권장 도구 | 이유 |
|-----------|-----------|------|
| 심볼 rename / move / find-refs | Serena MCP | LSP 기반 정확한 심볼 추적 |
| 패턴 기반 bulk edit (import 변경, API 교체, 스타일) | morphllm MCP (`mcp__morph-mcp__edit_file`) | 30-50% 토큰 절약, 멀티파일 일관성 |
| UI 컴포넌트 생성 | magic MCP | 21st.dev 패턴 활용 |
| 단일 파일 소규모 수정 | native Edit/MultiEdit | 가장 단순하고 빠름 |

**Serena + morphllm 조합** (대형 리팩터링 권장):
1. Serena `find_symbol` / `find_referencing_symbols` → 영향받는 파일 목록 확보
2. morphllm `edit_file` → 발견된 파일들에 패턴 일괄 적용

**중간 검증 게이트** (각 phase 종료 시):
- lint / typecheck / test 실행
- 실패 시 root-cause-analyst agent 호출

**TodoWrite 업데이트**: 각 todo 완료 시 즉시 `completed` 마킹

**보고 형식**:
```
## ⚙️ Execute
- 코드 편집 전략: <Serena/morphllm/magic/native> (이유: <한 줄>)
- 완료된 specialists: <agent-name N개>
- 검증 게이트: lint <✅/❌> / typecheck <✅/❌> / test <✅/❌>
```

### 단계 5: Review Phase (Critic 병렬 + Premium 검토)

**필수**:

1. **critic agent 병렬** (Opus generator 시):
   ```
   Task(subagent_type="critic", prompt="<직전 결과물 + falsifiability audit>")
   ```

2. **Premium model review** (중요 산출물 시):
   - OpenRouter 통해 Gemini 3.1 Pro / GPT 5.4 Pro 호출 (사용자가 명시 요청 시)
   - 또는 사용자에게 "Premium review 진행할까요?" 질문

**보고**:
```
## 🛡️ Review
- Critic: <verdict: Proceed/Revise/Reconsider>
- Falsifiability coverage: <X%>
- 수정 필요: <Y/N + 항목>
```

### 단계 6: Memory Update (학습 누적)

**Routing 규칙** (CLAUDE.md §Memory Routing):

- **코드/파일 위치/구조** → Serena `write_memory`
- **도메인 사실 (논문, 결정, 회의록)** → Graphiti `add_memory` (운영 가능 시) > Auto-memory
- **사용자 선호/feedback/lesson** → Auto-memory (`feedback_*.md`)
- **프로젝트 진행 상태** → Auto-memory (`*_project.md`)

**MEMORY.md 인덱스 업데이트**: 새 메모리 파일 추가 시 한 줄 링크 추가

**최종 보고**:
```
## 📌 Memory Update
- Auto-memory: <파일 경로>
- Graphiti: <episode UUID 또는 skip>
- Serena: <key>
- MEMORY.md: <업데이트 여부>
```

---

## 출력 요구사항

각 단계마다 위 보고 형식을 **명시적으로** 출력. 단계 스킵 시 이유 명시 ("Research 불필요: 정보 수집 작업 아님").

전체 종료 시 **Summary**:
```
## ✅ Workflow Complete
- 진행 단계: 6/6 (또는 N/6 + skip 사유)
- 산출물: <파일/문서/결정>
- 다음 액션: <follow-up 추천>
```

---

## 안티 패턴 (위반 시 self-correct)

- ❌ Memory check 생략 → 1단계 강제 진행
- ❌ 단일 context에서 3+ 검색 순차 처리 → Explore subagent 병렬로 위임
- ❌ Critic 검토 생략 (Opus generator) → 5단계 강제 진행
- ❌ Plan 없이 jump-to-implementation → 2단계 먼저 완료
- ❌ Memory update 누락 → 6단계 강제 진행
- ❌ 패턴 기반 bulk 편집에 Edit 도구 반복 사용 → morphllm MCP로 위임

---

## 참고

- 전체 워크플로우 정의: `~/.claude/CLAUDE.md` §Intelligent Complex Task Workflow
- Memory routing: `~/.claude/projects/-home-juke/memory/feedback_complex_task_workflow.md`
- Sub-agent 병렬 처리 원칙: `~/.claude/projects/-home-juke/memory/feedback_parallel_subagents.md`
- Skill 자동 활성화: `~/.claude/skills/coord/SKILL.md` (키워드 매칭 시)
