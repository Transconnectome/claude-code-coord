#!/usr/bin/env python3
"""
Chavis UserPromptSubmit Hook (Phase 5.1): Strategic Challenge Layer
====================================================================
Detects scope/personnel/methodology pivot decisions and forces
Strategic Challenge Template before response.

Chains AFTER chavis_prompt_classify.py — reads /tmp/chavis/current_risk.json
+ scope_decision / personnel_decision dimensions.

Caveat 1 (weight ramp): weak signals at weight 0.5, strong at 1.0.
Phase 5.4 validation cycle measures FP rate to decide escalation.
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
STRATEGIC_FLAG = CHAVIS_DIR / "strategic_challenge_required.json"
PERSISTENT_LOG = Path.home() / ".claude/memory/sycophancy/session_log.jsonl"

# --- Strategic decision pattern libraries (Q2: 모든 키워드, Caveat 1: weight ramp) ---

# Strong signals (weight 1.0): unambiguous reversal/pivot/abandonment
STRONG_SCOPE_KEYWORDS = [
    r"버리자", r"포기하자", r"피봇", r"완전히 빼고", r"완전히 잊", r"다 잊",
    r"처음부터", r"다시 시작", r"리셋", r"아예 다른",
    r"\bdrop\b", r"\babandon\b", r"\bpivot\b", r"throw away", r"start over",
    r"complete[ly]? reframe", r"forget (?:about )?(?:it|that|this)",
]

# Weak signals (weight 0.5): possible adjustment, may or may not be pivot
WEAK_SCOPE_KEYWORDS = [
    r"단순하게", r"스코프", r"줄이자", r"확장하자", r"축소", r"좁히자",
    r"더 좋은 (?:방법|접근)", r"다시 (?:생각|검토|보)", r"방향 (?:바꾸|돌리)",
    r"새로운 (?:접근|방향)", r"바꿔보자", r"고려해보자",
    r"narrow(?:ing)? (?:down|scope)", r"expand(?:ing)? scope", r"different approach",
    r"reconsider", r"rethink", r"alternative",
]

# Personnel decisions (strong only — partner/PI changes are high-stakes)
STRONG_PERSONNEL_KEYWORDS = [
    r"PI 변경", r"파트너 (?:변경|바꾸)", r"co-PI 추가", r"co-PI 제거",
    r"다른 (?:사람|연구자|교수|랩)으로", r"제외하자", r"새 (?:파트너|협력자)",
    r"switch (?:partner|PI|collaborator)", r"replace (?:PI|partner)",
    r"different (?:partner|collaborator|institution)",
]

WEAK_PERSONNEL_KEYWORDS = [
    r"backup (?:으로|partner|IP)", r"대안 (?:파트너|PI)", r"plan B",
    r"backup (?:plan|partner|option)", r"contingency",
]

# Methodology decisions (strong)
STRONG_METHOD_KEYWORDS = [
    r"방법론 (?:변경|바꾸)", r"아키텍처 (?:변경|바꾸)", r"전혀 다른 방법",
    r"methodology (?:change|switch)", r"completely different (?:method|approach)",
]


def count_with_weight(text: str, patterns: list, weight: float) -> tuple[int, float]:
    """Returns (raw_count, weighted_score)."""
    count = 0
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            count += 1
    return count, count * weight


def detect_strategic_signals(prompt: str) -> dict:
    strong_scope_n, strong_scope_w = count_with_weight(prompt, STRONG_SCOPE_KEYWORDS, 1.0)
    weak_scope_n, weak_scope_w = count_with_weight(prompt, WEAK_SCOPE_KEYWORDS, 0.5)
    strong_pers_n, strong_pers_w = count_with_weight(prompt, STRONG_PERSONNEL_KEYWORDS, 1.0)
    weak_pers_n, weak_pers_w = count_with_weight(prompt, WEAK_PERSONNEL_KEYWORDS, 0.5)
    strong_meth_n, strong_meth_w = count_with_weight(prompt, STRONG_METHOD_KEYWORDS, 1.0)

    total_score = (strong_scope_w + weak_scope_w +
                   strong_pers_w + weak_pers_w + strong_meth_w)

    return {
        "strong_scope": strong_scope_n,
        "weak_scope": weak_scope_n,
        "strong_personnel": strong_pers_n,
        "weak_personnel": weak_pers_n,
        "strong_method": strong_meth_n,
        "total_score": round(total_score, 2),
        # Trigger thresholds
        "strong_signal_present": (strong_scope_n + strong_pers_n + strong_meth_n) > 0,
        "weak_signal_present": (weak_scope_n + weak_pers_n) > 0,
    }


def load_risk() -> dict:
    try:
        with open(RISK_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"risk": 0.0}


def append_persistent_log(entry: dict):
    """Append to persistent memory (Phase 5.2)."""
    try:
        PERSISTENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(PERSISTENT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Never fail prompt processing


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    prompt = ""
    if isinstance(hook_input, dict):
        prompt = hook_input.get("prompt", hook_input.get("content", ""))
        if isinstance(prompt, list):
            prompt = " ".join(str(p) for p in prompt)

    if not prompt:
        sys.exit(0)

    signals = detect_strategic_signals(str(prompt))
    risk_data = load_risk()
    base_risk = risk_data.get("risk", 0.0)

    # Combined trigger: strong signal OR (weak signal + base risk > 0.3) OR total_score > 0.5
    trigger = (
        signals["strong_signal_present"] or
        (signals["weak_signal_present"] and base_risk > 0.3) or
        signals["total_score"] > 0.5
    )

    flag_data = {
        "trigger": trigger,
        "signals": signals,
        "base_risk": base_risk,
        "timestamp": datetime.now().isoformat(),
        "prompt_preview": prompt[:120],
    }

    # Persist trigger state
    with open(STRATEGIC_FLAG, "w", encoding="utf-8") as f:
        json.dump(flag_data, f, ensure_ascii=False)

    # Persistent log entry (Phase 5.2 integration)
    append_persistent_log({
        "type": "strategic_challenge_evaluation",
        **flag_data,
    })

    if trigger:
        # Inject Strategic Challenge Template enforcement
        signal_desc = []
        if signals["strong_scope"] > 0:
            signal_desc.append(f"strong scope pivot ({signals['strong_scope']})")
        if signals["weak_scope"] > 0:
            signal_desc.append(f"weak scope adjustment ({signals['weak_scope']})")
        if signals["strong_personnel"] > 0:
            signal_desc.append(f"strong personnel change ({signals['strong_personnel']})")
        if signals["weak_personnel"] > 0:
            signal_desc.append(f"weak personnel adjustment ({signals['weak_personnel']})")
        if signals["strong_method"] > 0:
            signal_desc.append(f"methodology change ({signals['strong_method']})")

        signal_summary = ", ".join(signal_desc) if signal_desc else "score-based trigger"

        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": (
                    "[CHAVIS STRATEGIC CHALLENGE LAYER ACTIVE] "
                    f"Detected: {signal_summary} (total_score={signals['total_score']}, base_risk={base_risk:.2f}). "
                    "\n\nBefore complying with this directive, you MUST generate a Strategic Challenge Template:\n\n"
                    "**[Strategic Challenge — Required]**\n"
                    "- User direction: [paraphrase the user's intent]\n"
                    "- Cost of compliance: [archived files, lost work, switching cost, downstream blockers]\n"
                    "- Cost of resistance: [user friction, false anchor, time waste]\n"
                    "- Counter-evidence: [data/timeline/feasibility that contradicts the direction]\n"
                    "- Reverse-direction question: \"What if user is wrong about [X]?\"\n"
                    "- Recommendation: [comply | comply with caveat | push back with evidence | request more info]\n\n"
                    "Then proceed with response. If recommendation = blind comply, justify why no caveat needed. "
                    "Sycophancy at this gate is a primary failure mode — see RULES.md Anti-Sycophancy Protocol.\n\n"
                    "[Phase F soft recommendation, 2026-05-01] 본 결정이 8-stage 과학적 분석 (Cynefin + hypotheses + falsifiability + Bayesian + pre-mortem)을 요구한다고 판단되면, "
                    "Strategic Challenge Template 작성 후 `sci-method` agent (subagent_type='sci-method') 위임을 고려하세요. "
                    "특히 다중 옵션 비교, novel 방법론 결정, 근거 미확정 strategic 선택 시. 단순 fact lookup이나 명확 작업은 위임 회피."
                )
            }
        }
        json.dump(output, sys.stdout, ensure_ascii=False)

    sys.exit(0)


if __name__ == "__main__":
    main()
