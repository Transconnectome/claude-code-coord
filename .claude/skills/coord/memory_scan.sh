#!/usr/bin/env bash
# memory_scan.sh — Auto-memory keyword search helper for /coord workflow.
# Usage: bash memory_scan.sh "<task description or keywords>"
# Output: Matched MEMORY.md entries + related feedback/lesson files.

set -euo pipefail

QUERY="${1:-}"
MEMORY_DIR="$HOME/.claude/projects/-home-juke/memory"
MEMORY_INDEX="$MEMORY_DIR/MEMORY.md"

if [[ -z "$QUERY" ]]; then
    echo "Usage: bash memory_scan.sh \"<task keywords>\""
    exit 1
fi

if [[ ! -f "$MEMORY_INDEX" ]]; then
    echo "WARN: MEMORY.md not found at $MEMORY_INDEX"
    exit 0
fi

# Extract 2-4 keywords (split on space, drop short/common words)
# Simple tokenizer — splits on whitespace + Korean particles.
KEYWORDS=$(echo "$QUERY" \
    | tr '[:upper:]' '[:lower:]' \
    | tr -s '[:space:][:punct:]' '\n' \
    | awk 'length($0) >= 3' \
    | grep -viE '^(the|and|for|with|이|가|을|를|은|는|에|의|로|으로|that|this|with|from|into|when|how|what|why|where)$' \
    | head -8 || true)

if [[ -z "$KEYWORDS" ]]; then
    echo "## 🧠 Memory Scan: no extractable keywords from \"$QUERY\""
    exit 0
fi

echo "## 🧠 Memory Scan: \"$QUERY\""
echo ""
echo "**Keywords**: $(echo "$KEYWORDS" | tr '\n' ' ')"
echo ""

# 1. Search MEMORY.md index for any keyword
echo "### MEMORY.md 인덱스 매치"
INDEX_HITS=$(grep -in -E "$(echo "$KEYWORDS" | tr '\n' '|' | sed 's/|$//')" "$MEMORY_INDEX" 2>/dev/null | head -10 || true)
if [[ -n "$INDEX_HITS" ]]; then
    echo "$INDEX_HITS"
else
    echo "(매치 없음)"
fi
echo ""

# 2. Search feedback files (sycophancy/usage feedback patterns)
echo "### 관련 feedback 파일 (lessons/preferences)"
FEEDBACK_HITS=$(find "$MEMORY_DIR" -maxdepth 2 -type f -name 'feedback_*.md' 2>/dev/null \
    | xargs -I{} grep -lE "$(echo "$KEYWORDS" | tr '\n' '|' | sed 's/|$//')" {} 2>/dev/null \
    | head -5 || true)
if [[ -n "$FEEDBACK_HITS" ]]; then
    echo "$FEEDBACK_HITS"
else
    echo "(매치 없음)"
fi
echo ""

# 3. Search project files (active work context)
echo "### 관련 프로젝트 파일"
PROJECT_HITS=$(find "$MEMORY_DIR" -maxdepth 2 -type f \( -name '*_project.md' -o -name '*_state*.md' -o -name '*_workflow.md' \) 2>/dev/null \
    | xargs -I{} grep -lE "$(echo "$KEYWORDS" | tr '\n' '|' | sed 's/|$//')" {} 2>/dev/null \
    | head -5 || true)
if [[ -n "$PROJECT_HITS" ]]; then
    echo "$PROJECT_HITS"
else
    echo "(매치 없음)"
fi
echo ""

# 4. Recent lessons (last 7 days)
echo "### 최근 7일 lessons (sycophancy/strategic)"
LESSONS_DIR="$MEMORY_DIR/sycophancy/lessons"
if [[ -d "$LESSONS_DIR" ]]; then
    RECENT_LESSONS=$(find "$LESSONS_DIR" -type f -name '*.md' -mtime -7 2>/dev/null | head -5 || true)
    if [[ -n "$RECENT_LESSONS" ]]; then
        echo "$RECENT_LESSONS"
    else
        echo "(최근 7일 lesson 없음)"
    fi
else
    echo "(lessons 디렉토리 없음)"
fi
echo ""

echo "---"
echo "다음 액션 권장: 위 매치된 파일 중 task와 가장 관련 있는 것 1-2개를 Read로 확인."
