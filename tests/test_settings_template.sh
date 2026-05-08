#!/usr/bin/env bash
# TDD tests for settings/settings.json.template
# Run from repo root: bash tests/test_settings_template.sh

set -uo pipefail

TEMPLATE="settings/settings.json.template"
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

echo "=== settings.json.template TDD Tests ==="
echo ""

# Prerequisite: file exists
if [[ ! -f "$TEMPLATE" ]]; then
    echo -e "${RED}FAIL${RESET} — Template file $TEMPLATE does not exist"
    exit 1
fi

# TC-01: Valid JSON after substituting placeholders
normalized=$(sed 's/{{[^}]*}}/PLACEHOLDER/g' "$TEMPLATE")
echo "$normalized" | python3 -m json.tool > /dev/null 2>&1
tc01_code=$?
run_test "TC-01: valid JSON after placeholder substitution" "$tc01_code" "0"

# TC-02: No real API keys present (security check)
real_keys=$(grep -E "tvly-[A-Za-z0-9]+|sk-[A-Za-z0-9]+|ghp_[A-Za-z0-9]+" "$TEMPLATE" 2>/dev/null || true)
if [[ -z "$real_keys" ]]; then
    run_test "TC-02: no real API keys in template" "clean" "clean"
else
    run_test "TC-02: no real API keys in template" "LEAKED:$real_keys" "clean"
fi

# TC-03: Required MCP servers present
required_mcps=("sequential-thinking" "tavily" "context7" "morphllm" "serena")
missing_mcps=()
for mcp in "${required_mcps[@]}"; do
    if ! grep -q "\"$mcp\"" "$TEMPLATE"; then
        missing_mcps+=("$mcp")
    fi
done
if [[ ${#missing_mcps[@]} -eq 0 ]]; then
    run_test "TC-03: required MCP servers present (sequential-thinking, tavily, context7, morphllm, serena)" "all-found" "all-found"
else
    run_test "TC-03: required MCP servers present" "missing:${missing_mcps[*]}" "all-found"
fi

# TC-04: Hooks section present
hook_events=("SessionStart" "UserPromptSubmit" "Stop")
missing_hooks=()
for event in "${hook_events[@]}"; do
    if ! grep -q "\"$event\"" "$TEMPLATE"; then
        missing_hooks+=("$event")
    fi
done
if [[ ${#missing_hooks[@]} -eq 0 ]]; then
    run_test "TC-04: hooks section (SessionStart, UserPromptSubmit, Stop) present" "all-found" "all-found"
else
    run_test "TC-04: hooks section present" "missing:${missing_hooks[*]}" "all-found"
fi

# TC-05: No hardcoded absolute /home/juke paths
hardcoded_paths=$(grep -E "/home/juke" "$TEMPLATE" 2>/dev/null | grep -v "PATH_TO\|PLACEHOLDER\|#\|example" || true)
if [[ -z "$hardcoded_paths" ]]; then
    run_test "TC-05: no hardcoded /home/juke paths" "clean" "clean"
else
    echo "  Note: Found /home/juke references (may need review): $hardcoded_paths"
    run_test "TC-05: no hardcoded /home/juke paths" "WARN" "clean"
fi

# TC-06: Placeholders use {{KEY}} format
placeholder_count=$(grep -oE "\{\{[A-Z_]+\}\}" "$TEMPLATE" 2>/dev/null | wc -l || echo "0")
if [[ "$placeholder_count" -gt 0 ]]; then
    run_test "TC-06: placeholders use {{KEY}} format ($placeholder_count found)" "found" "found"
else
    run_test "TC-06: placeholders use {{KEY}} format" "none-found" "found"
fi

echo ""
echo "=== Results: ${PASS} PASS / ${FAIL} FAIL ==="
if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
exit 0
