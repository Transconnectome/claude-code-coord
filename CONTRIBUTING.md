# Contributing to claude-code-coord

Thank you for your interest in contributing! (기여해주셔서 감사합니다!)

This repo documents the `/coord` Intelligent Complex Task Workflow for Claude Code.
Contributions are welcome in the form of docs improvements, bug fixes, and new examples.

---

## Ways to Contribute

### 1. Report Issues
- Open a GitHub issue with a clear description
- Include your OS, Claude Code version, and relevant settings

### 2. Improve Documentation
- Fix typos, clarify explanations, add examples
- Submit a PR with your changes

### 3. Share Usage Examples
- Add new examples to `examples/example_usage.md`
- Include: scenario, command, what happens at each stage

### 4. Improve Hook Scripts
- The Chavis hooks in `.claude/hooks/` are the anti-sycophancy system
- Improvements should be tested with the existing test framework
- New patterns in `AUTHORITY_PATTERNS`, `EMOTIONAL_PATTERNS`, etc. are welcome

### 5. Add MCP Server Integrations
- Document how to use new MCP servers with `/coord`
- Add to `docs/MCP_SERVERS.md`

---

## Development Workflow

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/claude-code-coord.git
cd claude-code-coord

# 2. Create a feature branch
git checkout -b feature/your-improvement

# 3. TDD: Write tests first
# Add tests to tests/test_*.sh

# 4. Implement changes

# 5. Run tests
bash tests/test_verify_setup.sh
bash tests/test_settings_template.sh
bash tests/test_memory_scan.sh

# 6. Submit PR
```

---

## TDD Policy

All changes must include tests. For shell scripts:
- Add test cases to `tests/test_*.sh`
- Follow the `run_test "description" "$result" "$expected"` pattern
- All tests must pass before PR merge

For Python hooks:
- Test with `python3 -m py_compile <file>` at minimum
- Behavioral tests welcome (stdin/stdout based)

---

## Code Style

### Shell Scripts
- Use `set -euo pipefail`
- Color output with the `GREEN/RED/RESET` variables
- Document each function with a one-line comment

### Python Hooks
- Follow PEP 8
- Type hints encouraged
- Keep hook logic simple — complex analysis should be in dedicated functions
- Hooks must always `sys.exit(0)` to avoid blocking Claude (except intentional errors)
- Never crash silently — use `except Exception: pass` at the top level

---

## Sensitive Information Policy

**NEVER include in PRs:**
- Real API keys (use `{{PLACEHOLDER}}` in templates)
- Personal paths like `/home/username/...`
- OAuth tokens, credentials files
- Personal email addresses

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
