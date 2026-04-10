#!/bin/bash
set -euo pipefail

# Hermes Session Start Hook
# Loads persistent memory and learned skills into Claude's context at session start.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
HERMES_DATA="$PROJECT_DIR/hermes_data"
MEMORY_DIR="$HERMES_DATA/memory"
SKILLS_DIR="$HERMES_DATA/learned-skills"

# Build context from memory files and learned skills
context=""

# Load MEMORY.md if it exists and has content
if [ -f "$MEMORY_DIR/MEMORY.md" ] && [ -s "$MEMORY_DIR/MEMORY.md" ]; then
  memory_content=$(cat "$MEMORY_DIR/MEMORY.md")
  memory_size=$(wc -c < "$MEMORY_DIR/MEMORY.md")
  context+="[Hermes Memory — Agent Knowledge (${memory_size}/2200 chars)]
${memory_content}
"
fi

# Load USER.md if it exists and has content
if [ -f "$MEMORY_DIR/USER.md" ] && [ -s "$MEMORY_DIR/USER.md" ]; then
  user_content=$(cat "$MEMORY_DIR/USER.md")
  user_size=$(wc -c < "$MEMORY_DIR/USER.md")
  context+="
[Hermes Memory — User Profile (${user_size}/1375 chars)]
${user_content}
"
fi

# List learned skills if any exist
if [ -d "$SKILLS_DIR" ]; then
  skill_list=""
  for skill_dir in "$SKILLS_DIR"/*/; do
    if [ -f "$skill_dir/SKILL.md" ]; then
      skill_name=$(basename "$skill_dir")
      skill_desc=$(grep "^description:" "$skill_dir/SKILL.md" 2>/dev/null | head -1 | sed 's/^description: *//')
      skill_list+="  - $skill_name: $skill_desc
"
    fi
  done

  if [ -n "$skill_list" ]; then
    context+="
[Hermes — Learned Skills]
${skill_list}"
  fi
fi

# Output context if we have any
if [ -n "$context" ]; then
  # Escape for JSON output
  escaped_context=$(echo "$context" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" 2>/dev/null || echo '""')
  echo "{\"additionalContext\": $escaped_context}"
else
  echo "{}"
fi
