---
type: index
---

# Knowledge Base

> Research, learnings, reference material, and institutional knowledge.

## How to Use

1. Create a new note in this folder
2. Apply the **Knowledge Base** template (`Ctrl/Cmd+P` > "Insert template" > Knowledge Base)
3. Tag by topic and source, link to relevant [[agents]] and [[projects]]

## Recent Entries

```dataview
TABLE topic, source
FROM "knowledge-base"
WHERE type = "knowledge"
SORT file.mtime DESC
LIMIT 15
```

## By Topic

```dataview
TABLE length(rows) AS "Count"
FROM "knowledge-base"
WHERE type = "knowledge"
GROUP BY topic
SORT length(rows) DESC
```

## Key Agents

| Agent | Why |
|-------|-----|
| [[senior_researcher_agent\|Senior Researcher]] | Produces research packages, verifies facts |
| [[trend_researcher_agent\|Trend Researcher]] | Tracks industry trends and opportunities |
| [[data_analyst_agent\|Data Analyst]] | Generates performance reports and analyses |
| [[seo_specialist_agent\|SEO Specialist]] | Keyword research and search intelligence |
| [[secretary_agent\|Secretary]] | Maintains the empire's document repository |

## Related

- [[Home]] | [[Organization Map]]
- Template: `_templates/Knowledge Base.md`
