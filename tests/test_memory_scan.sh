#!/usr/bin/env bash
# TDD tests for .claude/skills/coord/memory_scan.sh
# Run from repo root: bash tests/test_memory_scan.sh
# All tests must PASS before any commits.

set -uo pipefail

SCRIPT=".claude/skills/coord/memory_scan.sh"
PASS=0
FAIL=0

# Color output
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

echo "=== memory_scan.sh TDD Tests ==="
echo ""

# TC-01: No args → exit 1
bash "$SCRIPT" 2>/dev/null
tc01_code=$?
run_test "TC-01: no args → exit 1" "$tc01_code" "1"

# TC-02: Valid query → exit 0
bash "$SCRIPT" "coord workflow" > /dev/null 2>&1
tc02_code=$?
run_test "TC-02: valid query → exit 0" "$tc02_code" "0"

# TC-03: Output contains "Keywords" header (output format: **Keywords**: ...)
tc03_out=$(bash "$SCRIPT" "coord MCP workflow" 2>/dev/null)
if echo "$tc03_out" | grep -q "Keywords"; then
    run_test "TC-03: output contains 'Keywords' header" "match" "match"
else
    run_test "TC-03: output contains 'Keywords' header" "no-match" "match"
fi

# TC-04: Output contains MEMORY.md section header
tc04_out=$(bash "$SCRIPT" "coord" 2>/dev/null)
if echo "$tc04_out" | grep -q "MEMORY.md"; then
    run_test "TC-04: output contains 'MEMORY.md' section" "match" "match"
else
    run_test "TC-04: output contains 'MEMORY.md' section" "no-match" "match"
fi

# TC-05: Output contains feedback files section
tc05_out=$(bash "$SCRIPT" "workflow memory" 2>/dev/null)
if echo "$tc05_out" | grep -qiE "feedback|lesson"; then
    run_test "TC-05: output references feedback/lesson section" "match" "match"
else
    run_test "TC-05: output references feedback/lesson section" "no-match" "match"
fi

# TC-06: Short Korean particles filtered (output should handle gracefully)
bash "$SCRIPT" "나 는 이 가 을" > /dev/null 2>&1
tc06_code=$?
# Should exit 0 even with very short/filtered words (graceful handling)
run_test "TC-06: short/particle words → handled gracefully (exit 0)" "$tc06_code" "0"

# TC-07: Memory Scan header appears in output
tc07_out=$(bash "$SCRIPT" "coord mcp agent" 2>/dev/null)
if echo "$tc07_out" | grep -q "Memory Scan"; then
    run_test "TC-07: output contains 'Memory Scan' header" "match" "match"
else
    run_test "TC-07: output contains 'Memory Scan' header" "no-match" "match"
fi

echo ""
echo "=== Results: ${PASS} PASS / ${FAIL} FAIL ==="
if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
exit 0
