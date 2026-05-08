#!/usr/bin/env python3
"""PostToolUse hook — multi-marker session tracker (core/markers/composite/alert)."""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import (SESSION_STATS, AUDIT_LOG, sanitize_path, load_config,
                  fresh_session, is_session_stale, lock_and_load)
from markers import extract_change, get_new_code, update_cyclomatic, update_deps
from composite import compute_composite
from alert import decide_alert, render_alert
from strategic_layer import cached_score


def _read_input():
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return None


def _apply_change(stats, added, removed, file_path, new_code):
    stats["last_activity"] = datetime.now().isoformat()
    stats["loc_added"] = stats.get("loc_added", 0) + added
    stats["loc_removed"] = stats.get("loc_removed", 0) + removed
    stats["tool_calls"] = stats.get("tool_calls", 0) + 1
    if file_path and file_path not in stats.get("files_touched", []):
        stats.setdefault("files_touched", []).append(file_path)
    update_cyclomatic(stats, new_code)
    update_deps(stats, new_code)


def _trigger_strategic(stats, composite, cfg):
    if not cfg.get("strategic_enabled", False) or composite < cfg.get("strategic_threshold", 60):
        return
    cached = cached_score(stats["session_id"], cfg.get("strategic_cache_ttl", 300))
    if cached:
        stats["strategic_score"] = cached
        return
    script = Path(__file__).resolve().parents[1] / "strategic_layer.py"
    subprocess.Popen([sys.executable, str(script), stats["session_id"]],
                     stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)


def _write_audit(sid, tool_name, file_path, added, removed, composite, cc_max):
    audit = {"ts": datetime.now().isoformat(), "session": sid, "tool": tool_name,
             "file": file_path, "added": added, "removed": removed,
             "composite": composite, "cc_max": cc_max}
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(audit, ensure_ascii=False) + "\n")


def main() -> int:
    hi = _read_input()
    if hi is None:
        return 0
    cfg = load_config()
    tool_name = hi.get("tool_name", "")
    if tool_name not in cfg["tools_tracked"]:
        return 0
    tool_input = hi.get("tool_input", {}) or {}
    added, removed, file_path = extract_change(tool_input, tool_name)
    file_path = sanitize_path(file_path)
    new_code = get_new_code(tool_input, tool_name)
    alert_payload = None
    with lock_and_load(SESSION_STATS) as stats:
        if not stats or is_session_stale(stats, cfg["session_idle_minutes"]):
            stats.clear(); stats.update(fresh_session())
        _apply_change(stats, added, removed, file_path, new_code)
        stats["last_code"] = new_code[:1000]
        composite = compute_composite(stats, cfg)
        stats["marker_composite"] = composite
        _trigger_strategic(stats, composite, cfg)
        decision = decide_alert(composite, cfg["alert_levels"], stats.get("alerts_shown", []))
        if decision:
            _, stats["alerts_shown"] = decision
            alert_payload = (dict(stats), composite)
        sid = stats["session_id"]
    _write_audit(sid, tool_name, file_path, added, removed, composite,
                 stats.get("cyclomatic_max", 0))
    if alert_payload:
        print(render_alert(*alert_payload), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
