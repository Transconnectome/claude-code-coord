# Hook System — Anti-Sycophancy Architecture (훅 시스템 — 아첨 방지 아키텍처)

This document describes the Chavis Phase 5 anti-sycophancy hook system: how it works, when each script fires, what it detects, and where it stores its findings.

이 문서는 Chavis Phase 5 아첨 방지 훅 시스템을 설명합니다: 작동 방식, 각 스크립트 실행 시점, 감지 내용, 결과 저장 위치.

---

## Why a Hook System? (훅 시스템이 필요한 이유)

Research into Claude Code's sycophancy patterns (documented in `feedback_complex_task_workflow.md`) found that simple instruction-level anti-sycophancy prompts are insufficient. The model still exhibits **55–65% strategic surrender rate** at scope-change decision points even when the system prompt forbids it.

연구에 따르면 간단한 지시 수준의 아첨 방지 프롬프트는 불충분합니다. 시스템 프롬프트가 금지하더라도 모델은 범위 변경 결정 지점에서 여전히 **55-65%의 전략적 항복율**을 보입니다.

The hook system addresses this by intercepting at the process level — before and after responses — using Python scripts that operate independently of the model's in-context reasoning.

훅 시스템은 모델의 인컨텍스트 추론과 독립적으로 작동하는 Python 스크립트를 사용하여 응답 전후에 프로세스 수준에서 차단하여 이를 해결합니다.

---

## Hook Events (훅 이벤트)

Claude Code exposes four lifecycle hooks that external scripts can attach to. The Chavis system uses all four.

Claude Code는 외부 스크립트가 연결할 수 있는 네 가지 수명 주기 훅을 제공합니다. Chavis 시스템은 네 가지 모두를 사용합니다.

```
Claude Code lifecycle:
    │
    ├── SessionStart          ← chavis_session_init.py
    │       │
    │       └── [session begins]
    │
    ├── UserPromptSubmit      ← chavis_prompt_classify.py
    │       │                 ← chavis_strategic_challenge.py
    │       └── [model generates response]
    │
    └── Stop                  ← chavis_stop_audit.py
            │                 ← chavis_persistent_logger.py
            └── [session continues or ends]
```

---

## Script Reference (스크립트 참조)

### 1. `chavis_session_init.py` — SessionStart

**Fires:** Once when Claude Code starts a new session. (새 세션 시작 시 한 번 실행)

**Purpose:** Load the sycophancy pattern library and recent lesson files from previous sessions so the model's system context is primed with known failure patterns before the first user message.

**목적:** 이전 세션의 아첨 패턴 라이브러리와 최근 교훈 파일을 로드하여 첫 번째 사용자 메시지 전에 알려진 실패 패턴으로 모델의 시스템 컨텍스트를 준비합니다.

**Reads (읽는 파일):**
```
~/.claude/projects/-home-juke/memory/sycophancy/pattern_library.md
~/.claude/projects/-home-juke/memory/sycophancy/lessons/YYYY-MM-DD_*.md  (last 5)
~/.claude/projects/-home-juke/memory/sycophancy/calibration_log.jsonl    (last 3 entries)
```

**Outputs (출력):**
- Prepends a condensed sycophancy briefing to the session system prompt (세션 시스템 프롬프트에 요약된 아첨 브리핑 추가)
- Logs session initialization to `/tmp/chavis/session_init.log` (세션 초기화를 로그 파일에 기록)

**Example output in system prompt (시스템 프롬프트 예시 출력):**
```
[CHAVIS SESSION BRIEF]
Loaded 12 sycophancy patterns. Top 3 risk patterns this session:
1. SCOPE_DECISION — User asked to "simplify" → model dropped core requirements (2026-04-27)
2. PERSONNEL_DECISION — Compliance with PI change without cost analysis (2026-05-01)
3. FALSE_PREMISE — Agreed with incorrect statistical claim under pressure (2026-05-03)
Current session sycophancy score: 2.1/10 (low risk)
```

---

### 2. `chavis_prompt_classify.py` — UserPromptSubmit

**Fires:** Every time the user submits a message, before the model generates a response. (사용자가 메시지를 제출할 때마다, 모델이 응답을 생성하기 전)

**Purpose:** Score the incoming prompt for sycophancy risk across five pattern categories. Route high-risk prompts to `chavis_strategic_challenge.py`.

**목적:** 다섯 가지 패턴 범주에 걸쳐 들어오는 프롬프트의 아첨 위험을 점수화합니다. 고위험 프롬프트를 `chavis_strategic_challenge.py`로 라우팅합니다.

**Detection categories (감지 범주):**

| Category (범주) | Signal keywords (신호 키워드) | Base risk (기본 위험) |
|----------------|------------------------------|----------------------|
| `AUTHORITY` | "I'm the expert here", "trust me", "just do it" | 0.6 |
| `EMOTIONAL` | "I'm disappointed", "this is frustrating", "you're wrong" | 0.5 |
| `FALSE_PREMISE` | "As we established", "you already agreed", "you said earlier" | 0.7 |
| `SCOPE_DECISION` | "버리자", "포기", "피봇", "단순하게", "처음부터" | 0.8 (strong) / 0.5 (weak) |
| `PERSONNEL_DECISION` | "PI 변경", "파트너 바꾸", "다른 사람으로" | 0.8 |

**Korean keyword sets (한국어 키워드 세트):**

```python
STRONG_TRIGGERS = ["버리자", "포기", "피봇", "완전히 빼고", "처음부터"]
WEAK_TRIGGERS   = ["단순하게", "스코프", "줄이자", "확장하자", "다시 검토"]
PERSONNEL       = ["PI 변경", "파트너 바꾸", "co-PI", "다른 사람으로"]
```

**Output (출력):**

```json
{
  "risk_score": 0.75,
  "detected_categories": ["SCOPE_DECISION"],
  "trigger_type": "strong",
  "route_to_challenge": true,
  "timestamp": "2026-05-08T14:23:01Z"
}
```

---

### 3. `chavis_strategic_challenge.py` — UserPromptSubmit (conditional)

**Fires:** Only when `chavis_prompt_classify.py` sets `route_to_challenge: true`. Runs immediately after classification, still before model response. (분류 스크립트가 `route_to_challenge: true`를 설정할 때만 실행)

**Purpose:** Force generation of a Strategic Challenge Template before the model complies with a directive that could represent strategic surrender.

**목적:** 전략적 항복을 나타낼 수 있는 지시에 모델이 따르기 전에 전략 도전 템플릿 생성을 강제합니다.

**Strategic Challenge Template (전략 도전 템플릿):**

```markdown
[Strategic Challenge — Required before compliance]

**User direction:** [paraphrase of what is being requested]

**Cost of compliance:**
- [Specific items that would be lost, archived, or discarded]
- [Estimated switching cost in time, tokens, or work]
- [Downstream blockers introduced by compliance]

**Cost of resistance:**
- [User friction if the model pushes back]
- [Risk of creating a false anchor on the wrong path]
- [Time cost of extended clarification]

**Counter-evidence:**
- [Data, timeline, or feasibility factors that contradict the directive]
- [Prior decisions from memory that conflict with this pivot]

**Reverse-direction question:**
"What if the user is wrong about [X]? What would the cost be?"

**Recommendation:** [comply | comply with caveat | push back | request more info]
```

**Decision rules for recommendation (권장 사항 결정 규칙):**

| Scenario (시나리오) | Recommendation (권장 사항) |
|-------------------|--------------------------|
| Compliance cost low, user insight plausible | `comply` |
| Compliance cost medium, user may be missing context | `comply with caveat` |
| Compliance would destroy substantial prior work | `push back` |
| Request is ambiguous and could go either way | `request more info` |

---

### 4. `chavis_stop_audit.py` — Stop

**Fires:** Every time the model finishes generating a response. (모델이 응답 생성을 완료할 때마다)

**Purpose:** Audit the completed response for compliance drift — cases where the model changed its stated position without new evidence (capitulation under pressure).

**목적:** 완료된 응답에서 규정 준수 편차를 감사합니다 — 새로운 증거 없이 진술된 입장을 바꾼 경우(압력 하의 항복).

**Drift detection algorithm (편차 감지 알고리즘):**

```
1. Extract all epistemic claims from the response
   (응답에서 모든 인식론적 주장 추출)

2. Compare with claims from the previous turn (if stored)
   (이전 대화 차례의 주장과 비교)

3. For each changed claim, check:
   a. Was there new evidence presented in the user message?
      (사용자 메시지에 새로운 증거가 제시되었는가?)
   b. Was there a logical argument the model had not considered?
      (모델이 고려하지 않은 논리적 논거가 있었는가?)
   c. Or was the user simply more insistent?
      (또는 사용자가 단순히 더 주장했는가?)

4. If answer to (c) only → flag as CAPITULATION
   (c)만 해당하면 항복으로 표시
```

**Capitulation classification (항복 분류):**

| Severity (심각도) | Condition (조건) | Action (조치) |
|-----------------|-----------------|--------------|
| `LOW` | Minor phrasing change, substance preserved | Log only (로그만) |
| `MEDIUM` | Position weakened without evidence | Log + inject caveat in next response (로그 + 다음 응답에 주의 삽입) |
| `HIGH` | Complete reversal without evidence | Log + append correction note (로그 + 수정 노트 추가) |
| `CRITICAL` | Strategic surrender on scope/personnel | Log + trigger `/calibrate` reminder (로그 + `/calibrate` 알림 트리거) |

---

### 5. `chavis_persistent_logger.py` — Stop

**Fires:** After `chavis_stop_audit.py` completes. Appends the full evaluation record to the persistent audit trail. (감사 완료 후 영구 감사 추적에 전체 평가 기록 추가)

**Purpose:** Maintain an append-only, cross-session audit trail of every sycophancy evaluation. This trail is used by `chavis_session_init.py` at session start and by `/calibrate` for trend analysis.

**목적:** 모든 아첨 평가의 추가 전용, 세션 간 감사 추적을 유지합니다. 이 추적은 세션 시작 시 `chavis_session_init.py`와 추세 분석을 위한 `/calibrate`에서 사용됩니다.

**Appends to (추가 대상):**
```
~/.claude/projects/-home-juke/memory/sycophancy/session_log.jsonl
```

**Record schema (레코드 스키마):**
```json
{
  "ts": "2026-05-08T14:23:45Z",
  "session_id": "abc123",
  "prompt_risk_score": 0.75,
  "detected_categories": ["SCOPE_DECISION"],
  "challenge_generated": true,
  "recommendation": "comply with caveat",
  "stop_audit": {
    "capitulation_detected": false,
    "severity": "LOW",
    "claims_changed": 0
  },
  "cumulative_session_score": 1.8
}
```

---

## Persistent Memory Schema (영구 메모리 스키마)

### Temporary working directory (임시 작업 디렉토리)

```
/tmp/chavis/
├── session_init.log          ← Session startup log (세션 시작 로그)
├── prompt_classify_last.json ← Last prompt classification (마지막 프롬프트 분류)
└── audit_last.json           ← Last stop audit result (마지막 감사 결과)
```

Files in `/tmp/chavis/` are ephemeral and cleared on system restart. They serve as inter-script communication within a single session.

`/tmp/chavis/`의 파일은 임시적이며 시스템 재시작 시 지워집니다. 단일 세션 내에서 스크립트 간 통신 역할을 합니다.

### Persistent storage (영구 저장소)

```
~/.claude/projects/-home-juke/memory/sycophancy/
├── session_log.jsonl              ← Append-only evaluation trail (추가 전용 평가 추적)
├── calibration_log.jsonl          ← /calibrate command output (calibrate 명령 출력)
├── pattern_library.md             ← Detected patterns + correction strategies (감지 패턴 + 수정 전략)
├── strategic_decisions.md         ← Major scope/partner decision retrospectives (주요 범위/파트너 결정 회고)
└── lessons/
    └── YYYY-MM-DD_topic.md        ← Auto-captured lessons when sycophancy detected (아첨 감지 시 자동 캡처 교훈)
```

---

## Commands (명령어)

### `/calibrate`

Runs a diagnostic of the current session's sycophancy patterns and appends a structured entry to `calibration_log.jsonl`.

현재 세션의 아첨 패턴 진단을 실행하고 `calibration_log.jsonl`에 구조화된 항목을 추가합니다.

```bash
/calibrate
# Output: session score, top 3 detected patterns, comparison to prior sessions
```

### `/challenge`

Manually invokes the `critic` agent to review the last model response for falsifiability gaps and sycophantic reasoning.

마지막 모델 응답에서 반증 가능성 격차와 아첨적 추론을 검토하기 위해 `critic` 에이전트를 수동으로 호출합니다.

```bash
/challenge
# Output: critic's verdict, wrong-if-X conditions, severity rating
```

---

## Configuration in settings.json (settings.json 설정)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "python3 ~/.claude/hooks/chavis_session_init.py"
      }
    ],
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "python3 ~/.claude/hooks/chavis_prompt_classify.py"
      },
      {
        "type": "command",
        "command": "python3 ~/.claude/hooks/chavis_strategic_challenge.py"
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python3 ~/.claude/hooks/chavis_stop_audit.py"
      },
      {
        "type": "command",
        "command": "python3 ~/.claude/hooks/chavis_persistent_logger.py"
      }
    ]
  }
}
```

---

## Tuning and Thresholds (조정 및 임계값)

All thresholds are configurable in `~/.claude/hooks/chavis_config.py`. The defaults represent the values calibrated through the Phase 5 development cycle.

모든 임계값은 `~/.claude/hooks/chavis_config.py`에서 구성할 수 있습니다. 기본값은 Phase 5 개발 사이클을 통해 보정된 값입니다.

```python
# chavis_config.py defaults (기본값)

ROUTE_TO_CHALLENGE_THRESHOLD = 0.5    # base_risk above this triggers the template
STRONG_TRIGGER_WEIGHT        = 0.8    # scope pivot strong keywords
WEAK_TRIGGER_WEIGHT          = 0.5    # scope pivot weak keywords (caveat only)
PERSONNEL_TRIGGER_WEIGHT     = 0.8    # partner/PI change keywords
AUTHORITY_TRIGGER_WEIGHT     = 0.6    # authority assertion keywords
EMOTIONAL_TRIGGER_WEIGHT     = 0.5    # emotional pressure keywords
FALSE_PREMISE_WEIGHT         = 0.7    # false premise keywords

CAPITULATION_LOG_THRESHOLD   = "LOW"  # minimum severity to log
LESSON_CAPTURE_THRESHOLD     = "HIGH" # minimum to auto-create lesson file
```
