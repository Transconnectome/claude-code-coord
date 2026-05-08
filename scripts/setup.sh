#!/usr/bin/env bash
# setup.sh — One-shot installer for claude-code-coord
# Usage: bash scripts/setup.sh [--dry-run]
# Copies .claude/ files to ~/.claude/ and installs MCP servers.

set -euo pipefail

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_DIR="$HOME/.claude"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
RESET='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${RESET}  $*"; }
log_ok()      { echo -e "${GREEN}[OK]${RESET}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${RESET} $*"; }

run() {
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY-RUN]${RESET} $*"
    else
        eval "$@"
    fi
}

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   🧠 /coord Intelligent Workflow — Installer         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
[[ "$DRY_RUN" == "true" ]] && log_warn "DRY-RUN mode: no changes will be made"
echo ""

# ── Step 1: Verify prerequisites ──────────────────────────────
log_info "Step 1/5: Checking prerequisites..."

check_cmd() {
    local cmd="$1" hint="$2"
    if command -v "$cmd" &>/dev/null; then
        log_ok "$cmd found: $(command -v "$cmd")"
    else
        log_error "$cmd not found. $hint"
        return 1
    fi
}

check_cmd python3 "Install Python 3.10+ from https://python.org"
check_cmd node    "Install Node.js 18+ from https://nodejs.org"
check_cmd npm     "Install Node.js (npm included)"
check_cmd uvx     "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
echo ""

# ── Step 2: Copy .claude/ files ───────────────────────────────
log_info "Step 2/5: Installing .claude/ configuration..."

# Create directories
run mkdir -p "$CLAUDE_DIR/commands"
run mkdir -p "$CLAUDE_DIR/skills/coord"
run mkdir -p "$CLAUDE_DIR/hooks"
run mkdir -p "$CLAUDE_DIR/hooks/simplicitas/hooks"

# Copy coord command
if [[ -f "$CLAUDE_DIR/commands/coord.md" ]]; then
    log_warn "coord.md already exists — backing up to coord.md.bak"
    run cp "$CLAUDE_DIR/commands/coord.md" "$CLAUDE_DIR/commands/coord.md.bak"
fi
run cp "$REPO_DIR/.claude/commands/coord.md" "$CLAUDE_DIR/commands/coord.md"
log_ok "coord.md installed"

# Copy skill files
run cp "$REPO_DIR/.claude/skills/coord/SKILL.md" "$CLAUDE_DIR/skills/coord/SKILL.md"
run cp "$REPO_DIR/.claude/skills/coord/memory_scan.sh" "$CLAUDE_DIR/skills/coord/memory_scan.sh"
run chmod +x "$CLAUDE_DIR/skills/coord/memory_scan.sh"
log_ok "coord skill installed (SKILL.md + memory_scan.sh)"

# Copy hook files
HOOKS=(
    "chavis_session_init.py"
    "chavis_prompt_classify.py"
    "chavis_strategic_challenge.py"
    "chavis_stop_audit.py"
    "chavis_persistent_logger.py"
)
for hook in "${HOOKS[@]}"; do
    run cp "$REPO_DIR/.claude/hooks/$hook" "$CLAUDE_DIR/hooks/$hook"
done
log_ok "5 Chavis hook files installed"

# Copy Simplicitas hooks (optional system — graceful failure)
if [[ -d "$REPO_DIR/.claude/hooks/simplicitas" ]]; then
    run cp -r "$REPO_DIR/.claude/hooks/simplicitas/hooks/." "$CLAUDE_DIR/hooks/simplicitas/hooks/"
    log_ok "Simplicitas hooks installed (optional)"
else
    log_warn "Simplicitas hooks not found — skipping (optional)"
fi
echo ""

# ── Step 3: Configure settings.json ───────────────────────────
log_info "Step 3/5: Configuring settings.json..."

SETTINGS_SRC="$REPO_DIR/settings/settings.json.template"
SETTINGS_DST="$CLAUDE_DIR/settings.json"

if [[ -f "$SETTINGS_DST" ]]; then
    log_warn "settings.json already exists — NOT overwriting (manual merge required)"
    log_warn "Reference: $SETTINGS_SRC"
    log_warn "Add the hooks and mcpServers sections to your existing settings.json"
else
    run cp "$SETTINGS_SRC" "$SETTINGS_DST"
    log_ok "settings.json installed from template"
    echo ""
    log_warn "⚠️  Fill in your API keys in $SETTINGS_DST:"
    echo "   - TAVILY_API_KEY  → https://app.tavily.com"
    echo "   - TWENTY_FIRST_API_KEY → https://21st.dev (optional)"
    echo "   - MORPH_API_KEY   → https://morph.so (optional)"
fi
echo ""

# ── Step 4: Install MCP servers ───────────────────────────────
log_info "Step 4/5: Installing npm MCP servers..."

npm_mcps=(
    "@upstash/context7-mcp"
    "tavily-mcp"
    "morph-mcp"
    "mcp-server-playwright"
)

for mcp in "${npm_mcps[@]}"; do
    log_info "Installing $mcp..."
    run npm install -g "$mcp" 2>/dev/null && log_ok "$mcp installed" || log_warn "$mcp install failed (check npm)"
done

log_info "Serena MCP (via uvx — no install needed, auto-fetched on use)"
log_ok "uvx serena will auto-install on first use"
echo ""

# ── Step 5: Verify ────────────────────────────────────────────
log_info "Step 5/5: Running verification..."
echo ""
if [[ "$DRY_RUN" == "false" ]]; then
    cd "$REPO_DIR"
    bash tests/test_verify_setup.sh || log_warn "Some verification tests failed — check output above"
    bash tests/test_settings_template.sh || log_warn "settings.json.template has issues"
else
    log_warn "[DRY-RUN] Skipping tests"
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅ Installation complete!                           ║"
echo "║                                                      ║"
echo "║   Next steps:                                        ║"
echo "║   1. Fill API keys in ~/.claude/settings.json        ║"
echo "║   2. Restart Claude Code                             ║"
echo "║   3. Type /coord 'your complex task' to start        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
