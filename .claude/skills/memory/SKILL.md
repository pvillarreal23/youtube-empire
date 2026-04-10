---
name: memory
description: Persistent memory system for storing knowledge across sessions. Save agent observations, user preferences, project conventions, and learned patterns. Use when you learn something worth remembering, when the user shares a preference, or when you need to recall past knowledge.
allowed-tools: Bash(cat *) Bash(wc *) Bash(grep *) Read Write Edit Bash(mkdir *)
---

# Persistent Memory System

You have persistent memory stored in two files under `hermes_data/memory/`:

- **MEMORY.md** — Your observations: environment quirks, project conventions, tool patterns, debugging insights, architectural decisions. Max 2200 characters.
- **USER.md** — User profile: preferences, communication style, workflow habits, recurring requests. Max 1375 characters.

## Storage Format

Entries are separated by `§` (section sign) on its own line. Each entry is a concise, self-contained fact.

Example:
```
§
Project uses FastAPI backend with async SQLAlchemy and SQLite
§
Frontend is Next.js 16 with React 19 and Tailwind CSS 4
§
31 AI agents defined as markdown files in /agents/ directory
```

## How to Use Memory

### Save a memory

When you learn something worth persisting, append it to the appropriate file:

```bash
# Save to MEMORY.md (agent knowledge)
cat >> hermes_data/memory/MEMORY.md << 'ENTRY'
§
<concise fact to remember>
ENTRY

# Save to USER.md (user profile)
cat >> hermes_data/memory/USER.md << 'ENTRY'
§
<user preference or habit>
ENTRY
```

**Before saving, always:**
1. Read the current file to check for duplicates
2. Check current size with `wc -c hermes_data/memory/MEMORY.md`
3. If near the limit, remove outdated entries before adding new ones

### Recall memories

```bash
# Read all memories
cat hermes_data/memory/MEMORY.md

# Search for specific topic
grep -i "topic" hermes_data/memory/MEMORY.md hermes_data/memory/USER.md
```

### Remove a memory

Read the file, identify the entry to remove (between `§` delimiters), and edit it out.

### Check usage

```bash
wc -c hermes_data/memory/MEMORY.md hermes_data/memory/USER.md
```

Report as percentage: MEMORY.md is X/2200 chars (Y%), USER.md is X/1375 chars (Y%).

## When to Save Memories

Save memories **proactively** when you:
- Discover a project convention or pattern
- Learn how the user prefers things done
- Find a workaround for an environment quirk
- Make a key architectural decision
- Encounter a debugging insight that would help future sessions

Save memories **conservatively**:
- One fact per entry, concise (under 150 chars ideally)
- No task-specific state (use session context for that)
- No information already in CLAUDE.md or project docs
- Deduplicate before adding

## Arguments

- `$0` — Action: save, recall, search, list, usage, remove
- `$1` — Target: memory, user, or search query
- `$2` — Content (for save action)
