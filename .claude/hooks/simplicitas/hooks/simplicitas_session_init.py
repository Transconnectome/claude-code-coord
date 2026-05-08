#!/usr/bin/env python3
"""Simplicitas SessionStart hook — archive previous + reset session_stats.

Without this, statusline shows stale data. Audit log preserved. Previous
session's markers archived to history.jsonl for cross-session trend.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import SESSION_STATS, fresh_session
from cross_session import archive


def main() -> int:
    try:
        sys.stdin.read()
    except Exception:
        pass
    try:
        prev = json.loads(SESSION_STATS.read_text())
        archive(prev)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    SESSION_STATS.write_text(json.dumps(fresh_session(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
