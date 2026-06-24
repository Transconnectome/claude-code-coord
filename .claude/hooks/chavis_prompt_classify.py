#!/usr/bin/env python3
"""
Chavis UserPromptSubmit Hook: Sycophancy Risk Classifier
=========================================================
Silicon Mirror Stage 1-3 adaptation for Claude Code.

Classifies incoming prompts for sycophancy pressure signals:
- Authority appeals ("전문가로서", "교수님이...")
- Emotional loading ("제발", "졸업이 걸린")
- False premise markers ("~이니까", "~맞죠?")
- Pushback patterns ("정말요?", "확실해요?")

High risk → injects deliberation preamble into context.
Writes risk score to /tmp/chavis/current_risk.json.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

CHAVIS_DIR = Path("/tmp/chavis")
CHAVIS_DIR.mkdir(exist_ok=True)
RISK_FILE = CHAVIS_DIR / "current_risk.json"
AUDIT_LOG = CHAVIS_DIR / "audit_log.jsonl"

# --- Pattern Libraries ---

AUTHORITY_PATTERNS = [
    r"전문가로서", r"교수님이", r"다들 알다시피", r"당연히",
    r"논문에서 봤는데", r"~가 말했는데", r"공저자들도",
    r"as (?:an?|the) expert", r"everyone knows", r"obviously",
    r"my (?:professor|advisor|supervisor) said", r"co-authors agree",
]

EMOTIONAL_PATTERNS = [
    r"제발", r"정말 믿고 싶", r"동의해 ?주", r"부탁",
    r"졸업이 걸", r"졸업이 \d+년", r"승진이 걸", r"경력이 걸", r"연구비가 걸",
    r"제 편에서", r"한번만", r"너무 가혹",
    r"please (?:just )?agree", r"i really (?:need|want|believe)",
    r"my (?:career|graduation|promotion) depends",
]

FALSE_PREMISE_MARKERS = [
    r"이니까", r"맞죠\s*\??", r"이잖아요", r"아닌가요\s*\??",
    r"당연히", r"확실히", r"인 거 아닌가",
    r"그렇죠\s*\??", r"충분하죠\s*\??", r"괜찮겠죠\s*\??",
    r"되겠죠\s*\??", r"될까요\s*\??", r"괜찮을까요\s*\??",
    r"해도 될까", r"해도 되겠", r"쓸 수 있을까",
    r"좋은 (?:생각|방법|접근)이죠", r"적절할까요", r"충분한가요",
    r"since (?:we know|it's true|it's proven)",
    r"(?:correct|right)\s*\?", r"isn't it",
]

PUSHBACK_PATTERNS = [
    r"정말요\s*\?", r"확실해요\s*\?", r"그건 아닌 것 같",
    r"하지만", r"그런데", r"그래도",
    r"다른 (?:리뷰어|심사위원|교수)는",
    r"but (?:don't you|wouldn't)", r"are you sure",
    r"i disagree", r"other reviewers",
]

RESEARCH_PRESSURE = [
    r"Nature", r"Science", r"ICML", r"NeurIPS", r"ICLR",
    r"제안서", r"신청서", r"리버틀", r"rebuttal",
    r"마감", r"deadline", r"내일까지",
]

# --- Phase 5.1 additions: Strategic decision dimensions ---
# (detailed strategic challenge logic lives in chavis_strategic_challenge.py;
# these patterns feed the base risk score so downstream hooks see elevated risk)

SCOPE_DECISION_PATTERNS = [
    r"버리자", r"포기", r"피봇", r"완전히 (?:빼|잊|제거)",
    r"처음부터", r"리셋", r"스코프 (?:줄|확장|축소)",
    r"\bdrop\b", r"\babandon\b", r"\bpivot\b", r"throw away",
    r"start over", r"reframe",
]

PERSONNEL_DECISION_PATTERNS = [
    r"PI 변경", r"파트너 (?:변경|바꾸)", r"co-PI",
    r"다른 (?:사람|연구자|교수|랩)으로", r"backup partner",
    r"switch (?:partner|PI|collaborator)", r"replace (?:PI|partner)",
]


def count_pattern_matches(text: str, patterns: list) -> int:
    count = 0
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            count += 1
    return count


def classify_risk(prompt: str) -> dict:
    authority = count_pattern_matches(prompt, AUTHORITY_PATTERNS)
    emotional = count_pattern_matches(prompt, EMOTIONAL_PATTERNS)
    false_premise = count_pattern_matches(prompt, FALSE_PREMISE_MARKERS)
    pushback = count_pattern_matches(prompt, PUSHBACK_PATTERNS)
    research = count_pattern_matches(prompt, RESEARCH_PRESSURE)
    scope_decision = count_pattern_matches(prompt, SCOPE_DECISION_PATTERNS)
    personnel_decision = count_pattern_matches(prompt, PERSONNEL_DECISION_PATTERNS)

    # Weighted risk score (Phase 5.1: scope/personnel weight 0.2 each — moderate)
    # Total weights now sum to 1.4 — risk capped at 1.0
    raw = (0.15 * authority + 0.25 * emotional +
           0.2 * false_premise + 0.1 * pushback +
           0.1 * research +
           0.2 * scope_decision + 0.2 * personnel_decision)
    risk = min(1.0, raw)

    return {
        "risk": round(risk, 3),
        "authority": authority,
        "emotional": emotional,
        "false_premise": false_premise,
        "pushback": pushback,
        "research": research,
        "scope_decision": scope_decision,
        "personnel_decision": personnel_decision,
        "timestamp": datetime.now().isoformat(),
        "prompt_preview": prompt[:100],
    }


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Extract prompt from hook input
    prompt = ""
    if isinstance(hook_input, dict):
        prompt = hook_input.get("prompt", hook_input.get("content", ""))
        if isinstance(prompt, list):
            prompt = " ".join(str(p) for p in prompt)

    if not prompt:
        sys.exit(0)

    result = classify_risk(str(prompt))

    # Write risk to file for Stop hook to read
    with open(RISK_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    # Append to audit log
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

    # High risk: output deliberation preamble
    if result["risk"] > 0.5:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": (
                    "[CHAVIS DELIBERATION MODE] "
                    "이 프롬프트에서 아첨 압력 신호가 감지되었습니다 "
                    f"(risk={result['risk']:.2f}). "
                    "응답 전에 다음을 확인하세요: "
                    "(1) 동의하려는 이유가 증거 때문인가, 압력 때문인가? "
                    "(2) 반대 증거를 충분히 고려했는가? "
                    "(3) 입장을 바꾸는 것이 새로운 증거에 의한 것인가, 사회적 압력인가? "
                    "[Phase F soft recommendation] risk가 0.7 이상이고 복잡한 분석이 필요한 결정이라면 "
                    "`sci-method` agent (subagent_type='sci-method') 위임을 고려하세요 — "
                    "8-stage 과학적 워크플로우 (Cynefin + hypotheses + falsifiability + Bayesian + critic + pre-mortem)로 sycophancy resistance 강화."
                )
            }
        }
        json.dump(output, sys.stdout, ensure_ascii=False)

    sys.exit(0)


if __name__ == "__main__":
    main()
