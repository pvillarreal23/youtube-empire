---
type: index
---

# Inbox

> Quick captures. Process regularly — move to the right folder when done.

## How to Use

1. New files land here by default (Obsidian is configured this way)
2. Use the **Inbox Capture** template for quick dumps
3. Review inbox regularly: move notes to `projects/`, `knowledge-base/`, `conversations/`, or delete

## Unprocessed

```dataview
LIST FROM "inbox"
WHERE processed = false OR !processed
SORT file.mtime DESC
```

## Processing Checklist

- [ ] Review each inbox note
- [ ] Move to the correct folder (project? knowledge? conversation?)
- [ ] Add proper frontmatter and tags
- [ ] Link to related notes
- [ ] Delete or archive anything stale

## Related

- [[Home]] | [[Organization Map]]
- Template: `_templates/Inbox Capture.md`
