---
type: index
---

# Conversations

> Logs of important conversations — meetings, calls, DMs, collaborations.

## How to Use

1. Create a new note in this folder
2. Apply the **Conversation** template (`Ctrl/Cmd+P` > "Insert template" > Conversation)
3. Tag the platform, link action items to [[projects]] or [[daily-notes]]

## Recent Conversations

```dataview
TABLE with, platform, date
FROM "conversations"
WHERE type = "conversation"
SORT date DESC
LIMIT 15
```

## Key Agents

| Agent | Why |
|-------|-----|
| [[secretary_agent\|Secretary]] | Manages meeting notes, action items, follow-ups |
| [[community_manager_agent\|Community Manager]] | Captures audience feedback and sentiment |
| [[partnership_manager_agent\|Partnership Manager]] | Logs sponsor/partner conversations |
| [[ceo_agent\|CEO]] | Strategic meetings and external calls |

## Related

- [[Home]] | [[Organization Map]]
- Templates: `_templates/Conversation.md`, `_templates/Meeting Notes.md`
