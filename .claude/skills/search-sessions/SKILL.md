---
name: search-sessions
description: Search past session transcripts for context from previous conversations. Use when you need to recall what was discussed, decided, or built in earlier sessions. Also use when the user asks "remember when we..." or "what did we do about..."
allowed-tools: Bash(ls *) Bash(cat *) Bash(grep *) Bash(find *) Bash(wc *) Bash(head *) Bash(tail *) Read Grep
---

# Session History Search

Search through logged session transcripts to recall context from past conversations.

## How It Works

Session transcripts are stored in `hermes_data/sessions/` as JSONL files. Each file contains the conversation history from a past session with metadata.

## Searching Past Sessions

### List recent sessions

```bash
ls -lt hermes_data/sessions/*.jsonl 2>/dev/null | head -20
```

Or with more detail:

```bash
for f in hermes_data/sessions/*.jsonl; do
  if [ -f "$f" ]; then
    session_id=$(basename "$f" .jsonl)
    line_count=$(wc -l < "$f")
    mod_date=$(stat -c '%y' "$f" 2>/dev/null | cut -d' ' -f1)
    first_msg=$(head -1 "$f" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('content','')[:80])" 2>/dev/null || echo "")
    echo "[$mod_date] $session_id ($line_count lines) - $first_msg"
  fi
done
```

### Search by keyword

```bash
grep -ril "$ARGUMENTS" hermes_data/sessions/ 2>/dev/null
```

Then read the matching files for context:

```bash
grep -n "$ARGUMENTS" hermes_data/sessions/*.jsonl 2>/dev/null | head -20
```

### Search with context

```bash
grep -B2 -A2 "$ARGUMENTS" hermes_data/sessions/*.jsonl 2>/dev/null | head -50
```

### Read a specific session

```bash
cat hermes_data/sessions/<session-id>.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        msg = json.loads(line.strip())
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:200]
        print(f'[{role}] {content}')
        print('---')
    except: pass
" 2>/dev/null | head -100
```

## What to Search For

- Architectural decisions: "decided to use", "chose", "approach"
- Debugging sessions: "fixed", "bug", "error", "workaround"
- User preferences: "prefer", "always", "never", "style"
- Tool usage: specific tool names, commands, scripts
- Project milestones: "shipped", "deployed", "merged", "completed"

## Tips

- Sessions are logged by the `session-logger.sh` hook at session end
- Each session has a unique ID derived from the Claude Code session
- Newer sessions appear at the bottom of the directory listing
- Use `wc -l` to gauge session length before reading the whole thing

## Arguments

- `$ARGUMENTS` — Search query (keywords to search for across all sessions)
