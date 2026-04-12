---
type: index
---

# Daily Notes

> Daily journals for tracking focus, tasks, and progress.

## How to Use

1. Press `Ctrl/Cmd+P` > "Open today's daily note" to create/open today's entry
2. The **Daily Note** template is applied automatically
3. Link to [[projects]], [[conversations]], and agents as you go

## Recent Notes

```dataview
LIST FROM "daily-notes"
WHERE type = "daily-note"
SORT file.name DESC
LIMIT 14
```

## Key Agents

| Agent | Why |
|-------|-----|
| [[secretary_agent\|Secretary]] | Manages daily briefs, action item tracking |
| [[ceo_agent\|CEO]] | Sets daily/weekly priorities |
| [[project_manager_agent\|Project Manager]] | Tracks what's due today |

## Related

- [[Home]] | [[Organization Map]]
- Template: `_templates/Daily Note.md`
