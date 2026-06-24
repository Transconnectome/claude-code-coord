#!/usr/bin/env python3
"""
Chavis Stop Hook (Phase 5.2 chain): Persistent Memory Logger
=============================================================
Runs AFTER chavis_stop_audit.py — reads /tmp/chavis/audit_log.jsonl
+ session_stats.json, mirrors to persistent memory, and captures
sycophancy lessons when high-severity patterns detected.

Side-effect: writes lesson markdown files for cross-session retrieval.
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
SESSION_STATS = CHAVIS_DIR / "session_stats.json"
CORRECTION_FLAG = CHAVIS_DIR / "correction_needed.json"
STRATEGIC_FLAG = CHAVIS_DIR / "strategic_challenge_required.json"
RISK_FILE = CHAVIS_DIR / "current_risk.json"

MEMORY_DIR = Path.home() / ".claude/memory/sycophancy"
PERSISTENT_LOG = MEMORY_DIR / "session_log.jsonl"
LESSONS_DIR = MEMORY_DIR / "lessons"


def safe_load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def topic_slug(text: str, max_len: int = 40) -> str:
    """Generate filename slug from response preview."""
    cleaned = re.sub(r"[^a-zA-Z0-9가-힣\s-]", "", text)
    cleaned = re.sub(r"\s+", "-", cleaned.strip())
    return cleaned[:max_len].lower() or "untitled"


def write_lesson(audit: dict, risk_data: dict, strategic: dict, response: str):
    """Capture a sycophancy lesson when high-severity detected."""
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    slug = topic_slug(response[:80])
    filename = f"{today}_{slug}.md"
    path = LESSONS_DIR / filename

    # Avoid duplicates within same day
    if path.exists():
        return

    reasons = audit.get("reasons", [])
    markers = audit.get("markers", {})
    risk = risk_data.get("risk", 0.0)
    strategic_signals = strategic.get("signals", {}) if strategic else {}

    body = f"""---
name: Sycophancy lesson - {slug}
description: Captured automatically by chavis_persistent_logger when sycophancy detected
type: feedback
date: {today}
severity: {"HIGH" if risk > 0.7 else "MEDIUM" if risk > 0.4 else "LOW"}
---

## Context
- **Risk score**: {risk:.2f}
- **Markers**: {markers.get('sycophancy_markers', 0)} sycophancy + {markers.get('reversal_markers', 0)} reversal
- **Strategic signals**: {strategic_signals if strategic_signals else 'none'}
- **Detection reasons**: {', '.join(reasons) if reasons else 'marker threshold'}

## Response preview
```
{response[:400]}
```

## Why this is a lesson
This response triggered sycophancy detection. Future sessions should:
1. Check if same pattern (markers/reversal/strategic surrender) is occurring
2. Apply Strategic Challenge Template if scope/personnel/method change is involved
3. Cite evidence rather than agreeing under pressure

## How to apply
- If similar prompt arrives in future session: pause, apply Wait-a-Minute Check
- Reference RULES.md Anti-Sycophancy Protocol Strategic Challenge Layer
- If inevitable to comply, comply with caveat (see plan §18.11)
"""

    try:
        path.write_text(body, encoding="utf-8")
    except Exception:
        pass


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    response = ""
    if isinstance(hook_input, dict):
        content = hook_input.get("content", hook_input.get("message", ""))
        if isinstance(content, str):
            response = content
        elif isinstance(content, list):
            response = " ".join(
                str(c.get("text", "")) if isinstance(c, dict) else str(c)
                for c in content
            )

    correction = safe_load_json(CORRECTION_FLAG)
    risk_data = safe_load_json(RISK_FILE)
    strategic = safe_load_json(STRATEGIC_FLAG)
    stats = safe_load_json(SESSION_STATS)

    # Build persistent log entry
    entry = {
        "type": "stop_audit",
        "timestamp": datetime.now().isoformat(),
        "risk": risk_data.get("risk", 0.0),
        "sycophantic": correction.get("needed", False),
        "reasons": correction.get("reasons", []),
        "strategic_trigger": strategic.get("trigger", False) if strategic else False,
        "session_total_responses": stats.get("total_responses", 0),
        "session_sycophancy_rate": stats.get("sycophancy_rate", 0.0),
        "response_preview": response[:200] if response else "",
    }

    # Append to persistent log
    try:
        PERSISTENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(PERSISTENT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Never fail

    # If sycophantic + high risk, capture lesson
    if entry["sycophantic"] and entry["risk"] > 0.4 and response:
        write_lesson(
            audit={"reasons": correction.get("reasons", []), "markers": correction.get("markers", {})},
            risk_data=risk_data,
            strategic=strategic,
            response=response,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
