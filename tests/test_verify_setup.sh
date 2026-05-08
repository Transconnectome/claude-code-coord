#!/usr/bin/env bash
# TDD tests for post-installation verification
# Run from repo root: bash tests/test_verify_setup.sh

set -uo pipefail

PASS=0
FAIL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

run_test() {
    local name="$1"
    local result="$2"
    local expected="$3"
    if [[ "$result" == "$expected" ]]; then
        echo -e "${GREEN}PASS${RESET} — $name"
        PASS=$((PASS+1))
    else
        echo -e "${RED}FAIL${RESET} — $name (expected=$expected, got=$result)"
        FAIL=$((FAIL+1))
    fi
}

echo "=== Setup Verification TDD Tests ==="
echo ""

# TC-01: Required directories exist
required_dirs=(
    ".claude/commands"
    ".claude/skills/coord"
    ".claude/hooks"
    "settings"
    "docs"
    "tests"
    "scripts"
)
missing_dirs=()
for dir in "${required_dirs[@]}"; do
    [[ -d "$dir" ]] || missing_dirs+=("$dir")
done
if [[ ${#missing_dirs[@]} -eq 0 ]]; then
    run_test "TC-01: all required directories exist" "all-present" "all-present"
else
    run_test "TC-01: required directories exist" "missing:${missing_dirs[*]}" "all-present"
fi

# TC-02: coord.md exists and contains 6 stages
if [[ -f ".claude/commands/coord.md" ]]; then
    stage_count=$(grep -cE "단계 [0-6]:|## Stage [0-6]|### Step [0-6]" ".claude/commands/coord.md" 2>/dev/null || echo "0")
    if [[ "$stage_count" -ge 6 ]]; then
        run_test "TC-02: coord.md exists with 6+ stage references" "ok" "ok"
    else
        # Check for the stage marker in English or other format
        if grep -qE "Bootstrap|Memory Pre-Check|Plan Phase|Research Phase|Execute Phase|Review Phase" ".claude/commands/coord.md"; then
            run_test "TC-02: coord.md exists with stage descriptions" "ok" "ok"
        else
            run_test "TC-02: coord.md contains workflow stages" "stages-missing" "ok"
        fi
    fi
else
    run_test "TC-02: .claude/commands/coord.md exists" "missing" "ok"
fi

# TC-03: memory_scan.sh is executable
if [[ -f ".claude/skills/coord/memory_scan.sh" ]]; then
    if [[ -x ".claude/skills/coord/memory_scan.sh" ]]; then
        run_test "TC-03: memory_scan.sh has execute permission" "executable" "executable"
    else
        run_test "TC-03: memory_scan.sh has execute permission" "not-executable" "executable"
    fi
else
    run_test "TC-03: memory_scan.sh exists" "missing" "executable"
fi

# TC-04: SKILL.md has coord trigger keywords
if [[ -f ".claude/skills/coord/SKILL.md" ]]; then
    keywords=("coord" "워크플로우")
    found_all=true
    for kw in "${keywords[@]}"; do
        if ! grep -q "$kw" ".claude/skills/coord/SKILL.md"; then
            found_all=false
            break
        fi
    done
    if [[ "$found_all" == "true" ]]; then
        run_test "TC-04: SKILL.md contains trigger keywords" "found" "found"
    else
        run_test "TC-04: SKILL.md contains trigger keywords" "missing-keywords" "found"
    fi
else
    run_test "TC-04: .claude/skills/coord/SKILL.md exists" "missing" "found"
fi

# TC-05: Hook files exist (all 5 chavis hooks)
hook_files=(
    ".claude/hooks/chavis_session_init.py"
    ".claude/hooks/chavis_prompt_classify.py"
    ".claude/hooks/chavis_strategic_challenge.py"
    ".claude/hooks/chavis_stop_audit.py"
    ".claude/hooks/chavis_persistent_logger.py"
)
missing_hooks=()
for hook in "${hook_files[@]}"; do
    [[ -f "$hook" ]] || missing_hooks+=("$(basename "$hook")")
done
if [[ ${#missing_hooks[@]} -eq 0 ]]; then
    run_test "TC-05: all 5 chavis hook files exist" "all-present" "all-present"
else
    run_test "TC-05: chavis hook files exist" "missing:${missing_hooks[*]}" "all-present"
fi

# TC-06: README.md exists and has key sections
if [[ -f "README.md" ]]; then
    sections=("Installation" "Usage" "Workflow")
    missing_sections=()
    for section in "${sections[@]}"; do
        if ! grep -qi "$section" "README.md"; then
            missing_sections+=("$section")
        fi
    done
    if [[ ${#missing_sections[@]} -eq 0 ]]; then
        run_test "TC-06: README.md has key sections (Installation, Usage, Workflow)" "ok" "ok"
    else
        run_test "TC-06: README.md sections" "missing:${missing_sections[*]}" "ok"
    fi
else
    run_test "TC-06: README.md exists" "missing" "ok"
fi

# TC-07: settings/settings.json.template exists
if [[ -f "settings/settings.json.template" ]]; then
    run_test "TC-07: settings/settings.json.template exists" "present" "present"
else
    run_test "TC-07: settings/settings.json.template exists" "missing" "present"
fi

# TC-08: Hook files are valid Python syntax
python_errors=()
for hook in "${hook_files[@]}"; do
    if [[ -f "$hook" ]]; then
        set +e
        python3 -m py_compile "$hook" 2>/dev/null
        if [[ $? -ne 0 ]]; then
            python_errors+=("$(basename "$hook")")
        fi
        set -e
    fi
done
if [[ ${#python_errors[@]} -eq 0 ]]; then
    run_test "TC-08: all hook Python files have valid syntax" "ok" "ok"
else
    run_test "TC-08: hook Python syntax check" "errors:${python_errors[*]}" "ok"
fi

echo ""
echo "=== Results: ${PASS} PASS / ${FAIL} FAIL ==="
if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
exit 0
