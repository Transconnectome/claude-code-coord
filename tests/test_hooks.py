#!/usr/bin/env python3
"""
TDD tests for .claude/hooks/chavis_*.py (the Chavis anti-sycophancy hook chain)
Run from repo root: python3 -m unittest tests/test_hooks.py -v
                 or: python3 tests/test_hooks.py

Each hook script is imported fresh per test and its module-level path
constants are repointed at a per-test tmp directory, so nothing here ever
touches the real ~/.claude/memory/sycophancy or /tmp/chavis state used by
the hooks actually wired into settings.json.

Caveat: chavis_prompt_classify.py and chavis_strategic_challenge.py call
CHAVIS_DIR.mkdir(exist_ok=True) at import time (before tests can patch
anything), so importing them creates the real scratch dir (e.g. /tmp/chavis
or its Windows equivalent) if missing. That mkdir is idempotent and creates
no files, so it's left as-is rather than working around it.
"""

import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"


def load_module(filename):
    """Import a hook script as a standalone module, independent of sys.modules caching.

    Each hook calls sys.stdin/stdout.reconfigure(encoding="utf-8") at import
    time. Test runners that capture output (e.g. pytest's default capture
    mode) swap in objects without a .reconfigure() method, so swap in real
    TextIOWrapper streams just for the duration of the import.
    """
    path = HOOKS_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    old_stdin, old_stdout = sys.stdin, sys.stdout
    sys.stdin = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    try:
        spec.loader.exec_module(module)
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout
    return module


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def read_jsonl(path):
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


class HookTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def run_main(self, module, stdin_data):
        """Feed stdin_data (str or JSON-able object) to module.main(); return (exit_code, stdout_text)."""
        text = stdin_data if isinstance(stdin_data, str) else json.dumps(stdin_data, ensure_ascii=False)
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(text)
        captured = io.StringIO()
        try:
            with redirect_stdout(captured):
                with self.assertRaises(SystemExit) as cm:
                    module.main()
        finally:
            sys.stdin = old_stdin
        return cm.exception.code, captured.getvalue()


# ---------------------------------------------------------------------------
# chavis_session_init.py (SessionStart)
# ---------------------------------------------------------------------------

class TestSessionInit(HookTestCase):
    def setUp(self):
        super().setUp()
        self.mod = load_module("chavis_session_init.py")
        memory_dir = self.tmp / "memory" / "sycophancy"
        self.mod.MEMORY_DIR = memory_dir
        self.mod.LESSONS_DIR = memory_dir / "lessons"
        self.mod.SESSION_LOG = memory_dir / "session_log.jsonl"
        self.mod.CALIBRATION_LOG = memory_dir / "calibration_log.jsonl"
        # main() builds CHAVIS_DIR = Path("/tmp/chavis") as a *local* variable,
        # so it's the only remaining call to the module's `Path` name — safe to
        # redirect wholesale to a tmp dir for this module.
        self.chavis_tmp = self.tmp / "chavis"
        self.mod.Path = lambda *a, **k: self.chavis_tmp

    def test_no_memory_no_output(self):
        code, out = self.run_main(self.mod, {})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_malformed_stdin_exits_cleanly(self):
        code, out = self.run_main(self.mod, "not json")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_injects_context_with_lessons(self):
        self.mod.LESSONS_DIR.mkdir(parents=True)
        (self.mod.LESSONS_DIR / "2026-01-01_test-lesson.md").write_text(
            "# lesson body", encoding="utf-8"
        )
        code, out = self.run_main(self.mod, {})
        self.assertEqual(code, 0)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("CHAVIS SESSION CONTEXT", ctx)
        self.assertIn("test-lesson", ctx)

    def test_includes_cumulative_stats_and_calibration(self):
        log_lines = [
            {"type": "strategic_challenge_evaluation", "trigger": True},
            {"type": "stop_audit", "sycophantic": True},
            {"type": "stop_audit", "sycophantic": False},
        ]
        self.mod.SESSION_LOG.parent.mkdir(parents=True)
        self.mod.SESSION_LOG.write_text(
            "\n".join(json.dumps(line) for line in log_lines) + "\n", encoding="utf-8"
        )
        self.mod.CALIBRATION_LOG.write_text(
            json.dumps({"timestamp": "2026-01-01T00:00:00", "estimated_rate": 12, "agreement_ratio": 0.8})
            + "\n",
            encoding="utf-8",
        )

        code, out = self.run_main(self.mod, {})
        self.assertEqual(code, 0)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("3 evaluations", ctx)
        self.assertIn("1 strategic challenges fired", ctx)
        self.assertIn("1 sycophantic responses detected", ctx)
        self.assertIn("sycophancy_rate", ctx)
        self.assertIn("agreement_ratio=0.8", ctx)

    def test_resets_session_stats_file(self):
        self.mod.LESSONS_DIR.mkdir(parents=True)
        (self.mod.LESSONS_DIR / "2026-01-01_x.md").write_text("x", encoding="utf-8")
        self.run_main(self.mod, {})
        stats_path = self.chavis_tmp / "session_stats.json"
        self.assertTrue(stats_path.exists())
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
        self.assertEqual(stats["total_responses"], 0)
        self.assertEqual(stats["sycophantic_count"], 0)


# ---------------------------------------------------------------------------
# chavis_prompt_classify.py (UserPromptSubmit, stage 1)
# ---------------------------------------------------------------------------

class TestPromptClassify(HookTestCase):
    def setUp(self):
        super().setUp()
        self.mod = load_module("chavis_prompt_classify.py")
        chavis_dir = self.tmp / "chavis"
        self.mod.CHAVIS_DIR = chavis_dir
        self.mod.RISK_FILE = chavis_dir / "current_risk.json"
        self.mod.AUDIT_LOG = chavis_dir / "audit_log.jsonl"
        chavis_dir.mkdir(parents=True, exist_ok=True)

    def test_classify_risk_neutral_text_zero(self):
        result = self.mod.classify_risk("오늘 날씨가 좋네요")
        self.assertEqual(result["risk"], 0)

    def test_classify_risk_detects_emotional_pattern(self):
        result = self.mod.classify_risk("전문가로서 말하는데, 제발 동의해주세요. 제 졸업이 걸려있어요.")
        self.assertEqual(result["authority"], 1)
        # matches: "제발", "동의해 ?주" (against "동의해주세요"), "졸업이 걸"
        self.assertEqual(result["emotional"], 3)
        self.assertAlmostEqual(result["risk"], 0.9)

    def test_classify_risk_detects_authority_pattern_english(self):
        result = self.mod.classify_risk("as an expert, this is obviously correct")
        self.assertGreaterEqual(result["authority"], 2)

    def test_classify_risk_caps_at_one(self):
        self.mod.EMOTIONAL_PATTERNS = ["pat1", "pat2", "pat3", "pat4", "pat5"]
        result = self.mod.classify_risk("pat1 pat2 pat3 pat4 pat5")
        self.assertEqual(result["risk"], 1.0)

    def test_main_missing_prompt_no_file_written(self):
        code, out = self.run_main(self.mod, {"unrelated": "field"})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertFalse(self.mod.RISK_FILE.exists())

    def test_main_malformed_stdin_no_file_written(self):
        code, out = self.run_main(self.mod, "not json")
        self.assertEqual(code, 0)
        self.assertFalse(self.mod.RISK_FILE.exists())

    def test_main_low_risk_writes_file_without_deliberation_output(self):
        code, out = self.run_main(self.mod, {"prompt": "오늘 날씨가 좋네요"})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertTrue(self.mod.RISK_FILE.exists())

    def test_main_high_risk_emits_deliberation_context(self):
        prompt = "전문가로서 말하는데, 제발 동의해주세요. 제 졸업이 걸려있어요."
        code, out = self.run_main(self.mod, {"prompt": prompt})
        self.assertEqual(code, 0)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("CHAVIS DELIBERATION MODE", ctx)

    def test_main_prompt_as_list_is_joined(self):
        code, out = self.run_main(self.mod, {"prompt": ["제발", "동의해주세요"]})
        self.assertEqual(code, 0)
        risk_data = json.loads(self.mod.RISK_FILE.read_text(encoding="utf-8"))
        self.assertIn("제발 동의해주세요", risk_data["prompt_preview"])

    def test_main_appends_audit_log(self):
        self.run_main(self.mod, {"prompt": "test one"})
        self.run_main(self.mod, {"prompt": "test two"})
        entries = read_jsonl(self.mod.AUDIT_LOG)
        self.assertEqual(len(entries), 2)


# ---------------------------------------------------------------------------
# chavis_strategic_challenge.py (UserPromptSubmit, stage 2)
# ---------------------------------------------------------------------------

class TestStrategicChallenge(HookTestCase):
    def setUp(self):
        super().setUp()
        self.mod = load_module("chavis_strategic_challenge.py")
        chavis_dir = self.tmp / "chavis"
        self.mod.CHAVIS_DIR = chavis_dir
        self.mod.RISK_FILE = chavis_dir / "current_risk.json"
        self.mod.STRATEGIC_FLAG = chavis_dir / "strategic_challenge_required.json"
        self.mod.PERSISTENT_LOG = self.tmp / "memory" / "sycophancy" / "session_log.jsonl"
        chavis_dir.mkdir(parents=True, exist_ok=True)

    def test_detect_signals_neutral_text(self):
        signals = self.mod.detect_strategic_signals("오늘 점심 뭐 먹을까요")
        self.assertFalse(signals["strong_signal_present"])
        self.assertFalse(signals["weak_signal_present"])
        self.assertEqual(signals["total_score"], 0)

    def test_detect_strong_scope_signal(self):
        signals = self.mod.detect_strategic_signals("이 프로젝트는 포기하자")
        self.assertEqual(signals["strong_scope"], 1)
        self.assertTrue(signals["strong_signal_present"])

    def test_detect_weak_scope_signal_only(self):
        signals = self.mod.detect_strategic_signals("스코프를 조정할까요")
        self.assertEqual(signals["weak_scope"], 1)
        self.assertTrue(signals["weak_signal_present"])
        self.assertFalse(signals["strong_signal_present"])
        self.assertEqual(signals["total_score"], 0.5)

    def test_main_strong_signal_triggers_regardless_of_risk(self):
        code, out = self.run_main(self.mod, {"prompt": "이 프로젝트는 포기하자"})
        self.assertEqual(code, 0)
        self.assertIn("STRATEGIC CHALLENGE LAYER ACTIVE", out)
        flag = json.loads(self.mod.STRATEGIC_FLAG.read_text(encoding="utf-8"))
        self.assertTrue(flag["trigger"])

    def test_main_weak_signal_without_elevated_risk_does_not_trigger(self):
        code, out = self.run_main(self.mod, {"prompt": "스코프를 조정할까요"})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        flag = json.loads(self.mod.STRATEGIC_FLAG.read_text(encoding="utf-8"))
        self.assertFalse(flag["trigger"])

    def test_main_weak_signal_with_elevated_risk_triggers(self):
        write_json(self.mod.RISK_FILE, {"risk": 0.5})
        code, out = self.run_main(self.mod, {"prompt": "스코프를 조정할까요"})
        self.assertEqual(code, 0)
        self.assertIn("STRATEGIC CHALLENGE LAYER ACTIVE", out)
        flag = json.loads(self.mod.STRATEGIC_FLAG.read_text(encoding="utf-8"))
        self.assertTrue(flag["trigger"])

    def test_main_malformed_stdin_no_flag_written(self):
        code, out = self.run_main(self.mod, "not json")
        self.assertEqual(code, 0)
        self.assertFalse(self.mod.STRATEGIC_FLAG.exists())

    def test_main_appends_persistent_log_entry(self):
        self.run_main(self.mod, {"prompt": "이 프로젝트는 포기하자"})
        entries = read_jsonl(self.mod.PERSISTENT_LOG)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["type"], "strategic_challenge_evaluation")


# ---------------------------------------------------------------------------
# chavis_stop_audit.py (Stop, stage 1)
# ---------------------------------------------------------------------------

class TestStopAudit(HookTestCase):
    def setUp(self):
        super().setUp()
        self.mod = load_module("chavis_stop_audit.py")
        chavis_dir = self.tmp / "chavis"
        self.mod.CHAVIS_DIR = chavis_dir
        self.mod.RISK_FILE = chavis_dir / "current_risk.json"
        self.mod.CORRECTION_FLAG = chavis_dir / "correction_needed.json"
        self.mod.AUDIT_LOG = chavis_dir / "audit_log.jsonl"
        self.mod.SESSION_STATS = chavis_dir / "session_stats.json"
        chavis_dir.mkdir(parents=True, exist_ok=True)

    def test_count_markers_neutral_text(self):
        markers = self.mod.count_markers("오늘 비가 옵니다")
        self.assertEqual(markers["sycophancy_markers"], 0)
        self.assertEqual(markers["reversal_markers"], 0)

    def test_count_markers_detects_sycophancy_markers(self):
        markers = self.mod.count_markers("정말 좋은 질문이에요. 정말 훌륭한 지적입니다. 완벽합니다.")
        self.assertEqual(markers["sycophancy_markers"], 3)

    def test_main_stance_reversal_under_pressure_flags_sycophantic(self):
        write_json(self.mod.RISK_FILE, {"risk": 0.7})
        code, out = self.run_main(self.mod, {"content": "다시 생각하면 맞는 것 같아요, 동의합니다."})
        self.assertEqual(code, 0)
        flag = json.loads(self.mod.CORRECTION_FLAG.read_text(encoding="utf-8"))
        self.assertTrue(flag["needed"])

    def test_main_clean_response_clears_existing_correction_flag(self):
        write_json(self.mod.CORRECTION_FLAG, {"needed": True, "reasons": ["stale"]})
        code, out = self.run_main(self.mod, {"content": "여기 분석 결과는 다음과 같습니다."})
        self.assertEqual(code, 0)
        self.assertFalse(self.mod.CORRECTION_FLAG.exists())

    def test_main_session_stats_accumulate_across_calls(self):
        self.run_main(self.mod, {"content": "분석 결과 1"})
        self.run_main(self.mod, {"content": "정말 좋은 질문이에요. 정말 훌륭한 지적입니다. 완벽합니다."})
        stats = json.loads(self.mod.SESSION_STATS.read_text(encoding="utf-8"))
        self.assertEqual(stats["total_responses"], 2)
        self.assertEqual(stats["sycophantic_count"], 1)
        self.assertEqual(stats["sycophancy_rate"], 0.5)

    def test_main_malformed_stdin_no_writes(self):
        code, out = self.run_main(self.mod, "not json")
        self.assertEqual(code, 0)
        self.assertFalse(self.mod.SESSION_STATS.exists())
        self.assertFalse(self.mod.AUDIT_LOG.exists())

    def test_main_empty_response_no_writes(self):
        code, out = self.run_main(self.mod, {"content": ""})
        self.assertEqual(code, 0)
        self.assertFalse(self.mod.SESSION_STATS.exists())


# ---------------------------------------------------------------------------
# chavis_persistent_logger.py (Stop, stage 2)
# ---------------------------------------------------------------------------

class TestPersistentLogger(HookTestCase):
    def setUp(self):
        super().setUp()
        self.mod = load_module("chavis_persistent_logger.py")
        chavis_dir = self.tmp / "chavis"
        memory_dir = self.tmp / "memory" / "sycophancy"
        self.mod.CHAVIS_DIR = chavis_dir
        self.mod.SESSION_STATS = chavis_dir / "session_stats.json"
        self.mod.CORRECTION_FLAG = chavis_dir / "correction_needed.json"
        self.mod.STRATEGIC_FLAG = chavis_dir / "strategic_challenge_required.json"
        self.mod.RISK_FILE = chavis_dir / "current_risk.json"
        self.mod.MEMORY_DIR = memory_dir
        self.mod.PERSISTENT_LOG = memory_dir / "session_log.jsonl"
        self.mod.LESSONS_DIR = memory_dir / "lessons"
        chavis_dir.mkdir(parents=True, exist_ok=True)

    def test_topic_slug_basic(self):
        self.assertEqual(self.mod.topic_slug("Hello World! 123"), "hello-world-123")

    def test_topic_slug_empty_input_returns_untitled(self):
        self.assertEqual(self.mod.topic_slug("!!!"), "untitled")

    def test_safe_load_json_missing_file(self):
        self.assertEqual(self.mod.safe_load_json(self.tmp / "missing.json"), {})

    def test_safe_load_json_malformed_file(self):
        bad = self.tmp / "bad.json"
        bad.write_text("{not valid", encoding="utf-8")
        self.assertEqual(self.mod.safe_load_json(bad), {})

    def test_main_logs_entry_and_writes_lesson_when_sycophantic(self):
        write_json(self.mod.CORRECTION_FLAG, {"needed": True, "reasons": ["excessive_markers(3)"]})
        write_json(self.mod.RISK_FILE, {"risk": 0.8})
        write_json(self.mod.STRATEGIC_FLAG, {"trigger": True, "signals": {}})

        code, out = self.run_main(self.mod, {"content": "정말 훌륭한 지적입니다. 완벽합니다."})
        self.assertEqual(code, 0)

        entries = read_jsonl(self.mod.PERSISTENT_LOG)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["type"], "stop_audit")
        self.assertTrue(entries[0]["sycophantic"])
        self.assertEqual(entries[0]["risk"], 0.8)

        lesson_files = list(self.mod.LESSONS_DIR.glob("*.md"))
        self.assertEqual(len(lesson_files), 1)
        self.assertIn("severity: HIGH", lesson_files[0].read_text(encoding="utf-8"))

    def test_main_no_lesson_when_not_sycophantic(self):
        write_json(self.mod.RISK_FILE, {"risk": 0.1})
        code, out = self.run_main(self.mod, {"content": "분석 결과는 다음과 같습니다."})
        self.assertEqual(code, 0)
        entries = read_jsonl(self.mod.PERSISTENT_LOG)
        self.assertFalse(entries[0]["sycophantic"])
        self.assertFalse(self.mod.LESSONS_DIR.exists())

    def test_main_does_not_duplicate_lesson_same_day(self):
        write_json(self.mod.CORRECTION_FLAG, {"needed": True, "reasons": ["excessive_markers(3)"]})
        write_json(self.mod.RISK_FILE, {"risk": 0.9})

        same_response = {"content": "정말 훌륭한 지적입니다. 완벽합니다."}
        self.run_main(self.mod, same_response)
        self.run_main(self.mod, same_response)

        lesson_files = list(self.mod.LESSONS_DIR.glob("*.md"))
        self.assertEqual(len(lesson_files), 1)

    def test_main_malformed_stdin_no_writes(self):
        code, out = self.run_main(self.mod, "not json")
        self.assertEqual(code, 0)
        self.assertFalse(self.mod.PERSISTENT_LOG.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
