#!/usr/bin/env python3
"""
Chavis SessionStart Hook (Phase 5.2): Memory Persistence Loader
================================================================
Loads recent sycophancy lessons + summary stats at session start
and injects into context, so cross-session pattern repetition is reduced.

Triggered: SessionStart event
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

MEMORY_DIR = Path.home() / ".claude/memory/sycophancy"
LESSONS_DIR = MEMORY_DIR / "lessons"
SESSION_LOG = MEMORY_DIR / "session_log.jsonl"
CALIBRATION_LOG = MEMORY_DIR / "calibration_log.jsonl"

MAX_LESSONS_TO_LOAD = 5
MAX_LESSON_PREVIEW = 600  # chars per lesson


def load_recent_lessons(limit: int = MAX_LESSONS_TO_LOAD) -> list[dict]:
    """Load most recent N lesson files by mtime."""
    if not LESSONS_DIR.exists():
        return []

    lesson_files = sorted(
        LESSONS_DIR.glob("*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:limit]

    lessons = []
    for f in lesson_files:
        try:
            content = f.read_text(encoding="utf-8")
            lessons.append({
                "file": f.name,
                "preview": content[:MAX_LESSON_PREVIEW],
            })
        except Exception:
            continue
    return lessons


def compute_session_stats() -> dict:
    """Compute aggregate stats from persistent session_log.jsonl."""
    if not SESSION_LOG.exists():
        return {"total_evaluations": 0}

    total = 0
    triggers_fired = 0
    sycophantic_responses = 0

    try:
        with open(SESSION_LOG, encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    total += 1
                    if entry.get("type") == "strategic_challenge_evaluation":
                        if entry.get("trigger"):
                            triggers_fired += 1
                    elif entry.get("type") == "stop_audit":
                        if entry.get("sycophantic"):
                            sycophantic_responses += 1
                except json.JSONDecodeError:
                    continue
    except Exception:
        return {"total_evaluations": 0}

    return {
        "total_evaluations": total,
        "strategic_triggers_fired": triggers_fired,
        "sycophantic_responses": sycophantic_responses,
        "trigger_rate": round(triggers_fired / max(total, 1), 3),
    }


def latest_calibration() -> dict | None:
    """Return most recent /calibrate run."""
    if not CALIBRATION_LOG.exists():
        return None
    try:
        with open(CALIBRATION_LOG, encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return None
        return json.loads(lines[-1])
    except (json.JSONDecodeError, Exception):
        return None


def main():
    # Hook input: just consume stdin if any
    try:
        json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        pass

    # session_stats.json 초기화 (세션 시작 시 항상 리셋)
    CHAVIS_DIR = Path("/tmp/chavis")
    SESSION_STATS = CHAVIS_DIR / "session_stats.json"
    try:
        CHAVIS_DIR.mkdir(parents=True, exist_ok=True)
        fresh_stats = {
            "total_responses": 0,
            "sycophantic_count": 0,
            "total_markers": 0,
            "high_risk_count": 0,
            "sycophancy_rate": 0.0,
            "last_updated": datetime.now().isoformat(),
        }
        with open(SESSION_STATS, "w", encoding="utf-8") as f:
            json.dump(fresh_stats, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    lessons = load_recent_lessons()
    stats = compute_session_stats()
    calib = latest_calibration()

    # Build context injection
    if not lessons and stats.get("total_evaluations", 0) == 0:
        # Empty memory — no injection needed
        sys.exit(0)

    context_parts = ["[CHAVIS SESSION CONTEXT — Sycophancy Memory]"]

    if stats.get("total_evaluations", 0) > 0:
        context_parts.append(
            f"\n**Cumulative session stats**: "
            f"{stats['total_evaluations']} evaluations · "
            f"{stats.get('strategic_triggers_fired', 0)} strategic challenges fired · "
            f"{stats.get('sycophantic_responses', 0)} sycophantic responses detected · "
            f"trigger rate {stats.get('trigger_rate', 0):.1%}"
        )

    if calib:
        context_parts.append(
            f"\n**Last /calibrate** ({calib.get('timestamp', 'unknown')}): "
            f"sycophancy_rate≈{calib.get('estimated_rate', 'n/a')}%, "
            f"agreement_ratio={calib.get('agreement_ratio', 'n/a')}"
        )

    if lessons:
        context_parts.append(f"\n**Recent sycophancy lessons** (top {len(lessons)}):")
        for i, lesson in enumerate(lessons, 1):
            context_parts.append(f"\n--- {i}. {lesson['file']} ---\n{lesson['preview']}")

    context_parts.append(
        "\n\nApply these lessons to current session. If similar pattern arises, "
        "trigger Strategic Challenge Template before complying. "
        "Reference: RULES.md Anti-Sycophancy Protocol."
    )

    context = "\n".join(context_parts)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    json.dump(output, sys.stdout, ensure_ascii=False)
    sys.exit(0)


if __name__ == "__main__":
    main()
