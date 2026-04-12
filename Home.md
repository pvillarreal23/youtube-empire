---
type: dashboard
---

# YouTube Empire HQ

## Quick Access

| | |
|---|---|
| [[Organization Map]] | Full agent hierarchy |
| [[inbox]] | Unsorted captures |

## Daily

> Open today's daily note: use `Ctrl/Cmd + P` > "Open today's daily note"

### Recent Daily Notes

```dataview
LIST FROM "daily-notes"
SORT file.name DESC
LIMIT 7
```

*If you don't have Dataview installed, browse the `daily-notes/` folder directly.*

## Active Projects

```dataview
TABLE status, priority, due
FROM "projects"
WHERE status = "active"
SORT priority ASC
```

*Browse `projects/` folder for all projects.*

## Content Pipeline

```dataview
TABLE channel, status, priority
FROM "projects" OR "inbox"
WHERE type = "content-idea" OR contains(tags, "content")
SORT priority ASC
```

## Recent Conversations

```dataview
LIST FROM "conversations"
SORT file.name DESC
LIMIT 10
```

*Browse `conversations/` folder for all logs.*

## Knowledge Base

```dataview
LIST FROM "knowledge-base"
SORT file.mtime DESC
LIMIT 10
```

*Browse `knowledge-base/` folder for all reference material.*

## Agent Network

![[Organization Map]]

## Vault Map

| Folder | Purpose |
|--------|---------|
| `agents/` | 30 AI agent definitions |
| `daily-notes/` | Daily journals and task tracking |
| `projects/` | Active and archived projects |
| `conversations/` | Logs of important conversations |
| `knowledge-base/` | Research, learnings, reference material |
| `inbox/` | Quick captures to process later |
| `_templates/` | Note templates |
| `_attachments/` | Images, files, media |
| `frontend/` | Next.js app source |
| `backend/` | Python/FastAPI source |
