# Tests

TDD test suite for the `/coord` workflow system.
(TDD 원칙: 테스트 먼저, 구현 나중)

---

## Running Tests

From the repo root:

```bash
# Run all tests
bash tests/test_memory_scan.sh
bash tests/test_settings_template.sh
bash tests/test_verify_setup.sh
python3 -m unittest tests.test_hooks -v

# Or run all at once
for t in tests/test_*.sh; do bash "$t"; done
```

---

## Test Files

| File | What it tests | TC count |
|------|---------------|----------|
| `test_memory_scan.sh` | `.claude/skills/coord/memory_scan.sh` input/output | 7 |
| `test_settings_template.sh` | `settings/settings.json.template` validity + security | 6 |
| `test_verify_setup.sh` | Post-installation file/executable checks | 8 |
| `test_hooks.py` | `.claude/hooks/chavis_*.py` hook chain (risk classification, strategic challenge, stop audit, persistent logging) | 38 |

---

## Test Output Format

```
=== memory_scan.sh TDD Tests ===

PASS — TC-01: no args → exit 1
PASS — TC-02: valid query → exit 0
PASS — TC-03: output contains 'Keywords:'
...

=== Results: 7 PASS / 0 FAIL ===
```

---

## Adding New Tests

Follow the existing pattern:

```bash
# In tests/test_*.sh

run_test() {
    local name="$1" result="$2" expected="$3"
    if [[ "$result" == "$expected" ]]; then
        echo -e "${GREEN}PASS${RESET} — $name"; ((PASS++))
    else
        echo -e "${RED}FAIL${RESET} — $name (got=$result, want=$expected)"; ((FAIL++))
    fi
}

# Example test case
tc_out=$(some_command 2>/dev/null)
run_test "TC-N: description" "$(echo "$tc_out" | grep -c pattern)" "1"
```

---

## Test Philosophy

1. **Red → Green → Refactor**: Write failing test, implement, verify passing
2. **No mocking**: Tests use real files, real scripts
3. **Fast**: All tests complete in under 10 seconds
4. **Deterministic**: No randomness, no external API calls in core tests
5. **Security**: `test_settings_template.sh` TC-02 always checks for leaked API keys
