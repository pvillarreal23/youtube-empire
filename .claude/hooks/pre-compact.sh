#!/bin/bash
set -euo pipefail

# Hermes Pre-Compact Hook
# Before context window compression, save a summary of the current work
# to memory so critical context survives the compaction.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
MEMORY_FILE="$PROJECT_DIR/hermes_data/memory/MEMORY.md"

# Ensure memory directory exists
mkdir -p "$(dirname "$MEMORY_FILE")"

# Add a note that compaction happened (the agent can update memory with
# important context before this runs via the memory skill)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Only add compaction marker if memory file exists
if [ -f "$MEMORY_FILE" ]; then
  # Check if we already have a recent compaction note (within last entry)
  last_entry=$(tail -5 "$MEMORY_FILE" 2>/dev/null || echo "")
  if ! echo "$last_entry" | grep -q "Context compacted"; then
    cat >> "$MEMORY_FILE" << EOF
§
Context compacted at $TIMESTAMP — check memory for preserved context
EOF
  fi
fi

# Output guidance for Claude to preserve important context
echo '{"additionalContext": "Context is being compressed. Before continuing, use /memory to save any critical context (current task, key decisions, important file paths) that should survive compaction."}'
