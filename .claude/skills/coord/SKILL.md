---
name: coord
description: Intelligent Complex Task Workflow 활성화 (Memory + Sequential + Plan + Specialist Agents + Critic 6단계 파이프라인). 복잡한 구현/설계/디버깅/리팩터링/마이그레이션 작업 시 자동 활성화. /coord 명령으로 명시 호출도 가능.
trigger_keywords:
  - coord
  - 복잡한 작업
  - intelligent workflow
  - 워크플로우 활성화
  - 종합 분석
  - 시스템 설계
  - 아키텍처 설계
  - 마이그레이션 계획
  - 디버깅 워크플로우
  - 리팩터링 계획
language: ko
---

# coord — Intelligent Complex Task Workflow

복잡 작업 시 사용자가 정의한 **6단계 파이프라인**을 자동/반자동으로 가동합니다.
정의는 `~/.claude/CLAUDE.md` §Intelligent Complex Task Workflow를 참조.

## 호출 방식

### 1. 명시적 호출 (recommended)
```
/coord "<작업 설명>"
```
→ `/home/juke/.claude/commands/coord.md` 워크플로우 즉시 실행.

### 2. Skill 자동 활성화
사용자 prompt에 다음 키워드 포함 시 이 skill을 활성화하고 `/coord` 워크플로우 따라가기:
- "복잡한 작업" / "종합 분석" / "워크플로우"
- "시스템 설계" / "아키텍처" / "마이그레이션" / "리팩터링"
- "디버깅" + (multi-component / unclear cause)

### 3. 자동 판단 (heuristic)
다음 조건 중 2+ 충족 시 사용자에게 "이 작업은 `/coord` 워크플로우로 진행할까요?" 한 번 묻기:
- 3+ 단계 예상
- Multi-domain (frontend + backend + DB 등)
- Scope 모호 (요구사항 명확화 필요)
- 의사결정 (도구 선택, 아키텍처 trade-off)

단순 작업 (single file edit, fact lookup)은 활성화 **하지 말 것**.

## 워크플로우 6단계 (요약)

자세한 절차는 `/coord` slash command (`~/.claude/commands/coord.md`) 참조.

```
0. Bootstrap: ToolSearch로 graphiti + sequential-thinking 로드
1. Memory Pre-Check (병렬 3-source): Auto-memory + Serena + Graphiti
2. Plan Phase: sequential-thinking + Plan agent + TodoWrite 생성
3. Research Phase (필요 시): Explore 3+ + deep-research-agent 병렬
4. Execute Phase: Specialist agent 병렬 + 중간 검증 (lint/test)
5. Review Phase: critic agent + (선택) Premium model
6. Memory Update: Auto-memory > Graphiti > Serena 우선순위
```

## 도구 매핑

| 단계 | 핵심 도구 | Fallback |
|------|----------|----------|
| Memory | graphiti-memory, serena, Bash (memory_scan.sh) | Auto-memory grep |
| Plan | sequential-thinking, Plan agent | requirements-analyst |
| Research | Explore (병렬), deep-research-agent, tavily, context7 | WebSearch |
| Execute | backend/frontend-architect, python-expert, refactoring-expert | general-purpose |
| Review | critic, premium model (OpenRouter) | self-critic |
| Memory Update | Auto-memory write, graphiti add_memory, serena write_memory | local file |

## Memory Pre-Check 헬퍼

빠른 키워드 매칭은 다음 스크립트 사용:
```bash
bash /home/juke/.claude/skills/coord/memory_scan.sh "<task keywords>"
```
출력: 매칭된 MEMORY.md 항목 + 관련 feedback/lesson 파일 경로.

## 안티 패턴 차단

이 skill 활성화 시 다음 위반 자동 self-correct:
- Memory check 생략 → 1단계 강제 실행
- 단일 context 3+ 순차 검색 → Explore subagent 병렬 위임
- Critic 검토 생략 (Opus generator) → 5단계 강제 실행
- Plan 없이 implementation → 2단계 먼저 완료
- Memory update 누락 → 6단계 강제 실행

## 비활성화 방법

Skill 자체를 비활성화하려면:
```bash
mv /home/juke/.claude/skills/coord /home/juke/.claude/skills/.coord-disabled
```
slash command만 비활성화:
```bash
mv /home/juke/.claude/commands/coord.md /home/juke/.claude/commands/.coord.md.disabled
```
완전 제거: 위 두 파일 삭제 + 이 skill 디렉토리 삭제.

## 검증 체크리스트

설치 직후 동작 확인:
- [ ] `/coord help` 입력 시 slash command 인식 (`coord.md` 내용 표시)
- [ ] `/coord "test task"` 입력 시 6단계 보고 형식 출력
- [ ] Bash로 `bash /home/juke/.claude/skills/coord/memory_scan.sh "test"` 실행 성공
- [ ] "복잡한 시스템 설계" prompt 시 skill auto-activation 동작
- [ ] Chavis hooks (settings.json) 영향 없음 — `/calibrate` 정상 동작
- [ ] Simplicitas hooks 영향 없음 — Edit 후 hook fire 정상

## 관련 파일

- Slash command: `/home/juke/.claude/commands/coord.md`
- Memory scan helper: `/home/juke/.claude/skills/coord/memory_scan.sh`
- 워크플로우 정의: `~/.claude/CLAUDE.md` §Intelligent Complex Task Workflow
- Memory routing: `~/.claude/projects/-home-juke/memory/feedback_complex_task_workflow.md`
- Parallel subagent 원칙: `~/.claude/projects/-home-juke/memory/feedback_parallel_subagents.md`
