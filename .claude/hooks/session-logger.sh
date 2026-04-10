#!/bin/bash
set -euo pipefail

# Hermes Session Logger Hook
# Logs session metadata and transcript for future search.
# Runs on Stop event to capture completed conversations.

input=$(cat)

SESSION_ID=$(echo "$input" | jq -r '.session_id // empty')
TRANSCRIPT_PATH=$(echo "$input" | jq -r '.transcript_path // empty')
CWD=$(echo "$input" | jq -r '.cwd // empty')

# Bail if no session ID
if [ -z "$SESSION_ID" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SESSIONS_DIR="$PROJECT_DIR/hermes_data/sessions"
mkdir -p "$SESSIONS_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SESSION_FILE="$SESSIONS_DIR/${SESSION_ID}.jsonl"

# If transcript exists, copy relevant parts
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
  # Extract user and assistant messages (skip tool calls for brevity)
  python3 -c "
import sys, json

with open('$TRANSCRIPT_PATH', 'r') as f:
    for line in f:
        try:
            msg = json.loads(line.strip())
            role = msg.get('role', '')
            content = msg.get('content', '')
            if role in ('user', 'assistant') and content:
                record = {
                    'role': role,
                    'content': content[:2000],
                    'session_id': '$SESSION_ID',
                    'timestamp': '$TIMESTAMP'
                }
                print(json.dumps(record))
        except (json.JSONDecodeError, KeyError):
            pass
" >> "$SESSION_FILE" 2>/dev/null || true
fi

# Write session metadata
META_FILE="$SESSIONS_DIR/${SESSION_ID}.meta.json"
cat > "$META_FILE" << EOF
{
  "session_id": "$SESSION_ID",
  "timestamp": "$TIMESTAMP",
  "cwd": "$CWD",
  "transcript_path": "$TRANSCRIPT_PATH"
}
EOF

exit 0
