---
type: index
---

# Projects

> Active initiatives and tracked work across the empire.

## How to Use

1. Create a new note in this folder
2. Apply the **Project** template (`Ctrl/Cmd+P` > "Insert template" > Project)
3. Link related [[agents]], [[conversations]], and [[knowledge-base]] entries

## Active Projects

```dataview
TABLE status, priority, due
FROM "projects"
WHERE status = "active" AND type = "project"
SORT priority ASC
```

## Completed Projects

```dataview
TABLE status, due
FROM "projects"
WHERE status = "completed"
SORT file.mtime DESC
LIMIT 10
```

## Key Agents

| Agent | Role |
|-------|------|
| [[project_manager_agent\|Project Manager]] | Tracks all projects, timelines, dependencies |
| [[workflow_orchestrator_agent\|Workflow Orchestrator]] | Designs and runs production pipelines |
| [[operations_vp_agent\|Operations VP]] | Oversees all operational projects |
| [[ceo_agent\|CEO]] | Approves strategic initiatives |

## Related

- [[Home]] | [[Organization Map]]
- Template: `_templates/Project.md`
