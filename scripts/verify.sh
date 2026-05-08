#!/usr/bin/env bash
# verify.sh — Post-installation verification script
# Run from repo root after setup.sh to confirm everything is in place.
# Usage: bash scripts/verify.sh

set -euo pipefail

PASS=0
FAIL=0
WARN=0

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
RESET='\033[0m'

check_ok()   { echo -e "${GREEN}  ✓${RESET} $*"; ((PASS++)); }
check_fail() { echo -e "${RED}  ✗${RESET} $*"; ((FAIL++)); }
check_warn() { echo -e "${YELLOW}  ⚠${RESET} $*"; ((WARN++)); }

echo ""
echo "🔍 /coord Installation Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Section 1: Core files
echo "📁 Core Files"
CLAUDE="$HOME/.claude"

[[ -f "$CLAUDE/commands/coord.md" ]] && check_ok "coord.md command installed" || check_fail "coord.md missing → bash scripts/setup.sh"
[[ -f "$CLAUDE/skills/coord/SKILL.md" ]] && check_ok "coord SKILL.md installed" || check_fail "SKILL.md missing"
[[ -x "$CLAUDE/skills/coord/memory_scan.sh" ]] && check_ok "memory_scan.sh executable" || check_fail "memory_scan.sh not found or not executable"
echo ""

# Section 2: Hook files
echo "🪝 Hook Files"
HOOKS=(
    "chavis_session_init.py"
    "chavis_prompt_classify.py"
    "chavis_strategic_challenge.py"
    "chavis_stop_audit.py"
    "chavis_persistent_logger.py"
)
for hook in "${HOOKS[@]}"; do
    [[ -f "$CLAUDE/hooks/$hook" ]] && check_ok "$hook" || check_fail "$hook missing"
done
[[ -f "$CLAUDE/hooks/simplicitas/hooks/simplicitas_track.py" ]] && check_ok "simplicitas_track.py" || check_warn "simplicitas_track.py missing (optional)"
echo ""

# Section 3: MCP servers
echo "🔌 MCP Servers (npm)"
MCP_CMDS=(
    "tavily-mcp:tavily"
    "context7-mcp:context7"
    "morph-mcp:morphllm"
    "mcp-server-playwright:playwright"
)
for pair in "${MCP_CMDS[@]}"; do
    cmd="${pair%%:*}"
    name="${pair##*:}"
    if command -v "$cmd" &>/dev/null 2>&1; then
        check_ok "$name ($cmd)"
    else
        # Check npm global
        if npm list -g "$cmd" &>/dev/null 2>&1; then
            check_ok "$name (npm global)"
        else
            check_warn "$name not found → npm install -g $cmd"
        fi
    fi
done
command -v uvx &>/dev/null && check_ok "uvx (for serena)" || check_warn "uvx not found → curl -LsSf https://astral.sh/uv/install.sh | sh"
echo ""

# Section 4: settings.json
echo "⚙️  Settings"
SETTINGS="$CLAUDE/settings.json"
if [[ -f "$SETTINGS" ]]; then
    check_ok "settings.json exists"
    # Check for hooks
    if grep -q "chavis_session_init" "$SETTINGS"; then
        check_ok "Chavis hooks configured in settings.json"
    else
        check_warn "Chavis hooks not found in settings.json — merge from settings/settings.json.template"
    fi
    # Check for MCP servers
    if grep -q "sequential-thinking" "$SETTINGS"; then
        check_ok "sequential-thinking MCP configured"
    else
        check_warn "sequential-thinking MCP missing in settings.json"
    fi
    # Check for API key placeholders (not filled)
    if grep -qE "\{\{[A-Z_]+\}\}" "$SETTINGS"; then
        check_warn "API key placeholders not filled in settings.json → edit with real keys"
    fi
else
    check_fail "settings.json missing → bash scripts/setup.sh"
fi
echo ""

# Section 5: Python syntax check
echo "🐍 Python Syntax"
for hook in "${HOOKS[@]}"; do
    filepath="$CLAUDE/hooks/$hook"
    if [[ -f "$filepath" ]]; then
        if python3 -m py_compile "$filepath" 2>/dev/null; then
            check_ok "$hook syntax valid"
        else
            check_fail "$hook has syntax errors"
        fi
    fi
done
echo ""

# Section 6: Quick functional test
echo "⚡ Functional Test"
if [[ -x "$CLAUDE/skills/coord/memory_scan.sh" ]]; then
    set +e
    out=$(bash "$CLAUDE/skills/coord/memory_scan.sh" "coord test query" 2>/dev/null)
    if echo "$out" | grep -q "Memory Scan"; then
        check_ok "memory_scan.sh functional test passed"
    else
        check_warn "memory_scan.sh output unexpected (MEMORY.md may not exist yet)"
    fi
    set -e
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Results: ${GREEN}${PASS} passed${RESET} · ${YELLOW}${WARN} warnings${RESET} · ${RED}${FAIL} failed${RESET}"
echo ""
if [[ $FAIL -gt 0 ]]; then
    echo "❌ Installation incomplete. Run: bash scripts/setup.sh"
    exit 1
elif [[ $WARN -gt 0 ]]; then
    echo "⚠️  Installation mostly complete. Review warnings above."
    exit 0
else
    echo "✅ All checks passed! Restart Claude Code and use /coord"
    exit 0
fi
