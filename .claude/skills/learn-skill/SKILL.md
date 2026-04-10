---
name: learn-skill
description: Create reusable skills from successful patterns. After completing a complex task well, use this to save the approach as a reusable skill for future sessions. Use when you want to teach yourself a new capability or save a proven pattern.
allowed-tools: Bash(mkdir *) Write Read Glob Bash(ls *) Bash(cat *) Bash(rm *)
---

# Skill Learning System

Create new Claude Code skills from successful patterns and solutions. Skills are saved as SKILL.md files that Claude Code loads automatically in future sessions.

## How Skill Learning Works

1. You complete a complex task successfully
2. You extract the reusable pattern (the "what" and "how")
3. You create a new skill file with clear instructions
4. Future sessions automatically discover and can use this skill

## Creating a New Skill

### Step 1: Identify the pattern

Ask yourself:
- Was this task complex enough to benefit from saved instructions?
- Would I (or another session) benefit from having these steps pre-written?
- Is this pattern reusable across different projects or contexts?

### Step 2: Create the skill directory and file

```bash
SKILL_NAME="$0"  # e.g., "api-scaffolder", "test-generator", "migration-builder"
mkdir -p hermes_data/learned-skills/$SKILL_NAME
```

### Step 3: Write the SKILL.md

Create `hermes_data/learned-skills/$SKILL_NAME/SKILL.md` with this structure:

```markdown
---
name: <skill-name>
description: <one-line description of what this skill does and when to use it>
allowed-tools: <tools this skill needs, e.g., Bash Write Read Edit Glob Grep>
---

# <Skill Name>

## When to Use
<Describe the trigger conditions — when should Claude activate this skill?>

## Steps
<Clear, numbered steps for executing the pattern>

## Example
<A concrete example of input/output>

## Notes
<Edge cases, gotchas, or variations>
```

### Step 4: Verify the skill

```bash
cat hermes_data/learned-skills/$SKILL_NAME/SKILL.md
```

Confirm the SKILL.md has valid YAML frontmatter and clear instructions.

## Listing Learned Skills

```bash
for skill_dir in hermes_data/learned-skills/*/; do
  if [ -f "$skill_dir/SKILL.md" ]; then
    name=$(basename "$skill_dir")
    desc=$(head -5 "$skill_dir/SKILL.md" | grep "description:" | sed 's/description: //')
    echo "- $name: $desc"
  fi
done
```

## Refining a Skill

Read the existing SKILL.md, identify what to improve, and edit it:

```bash
cat hermes_data/learned-skills/<name>/SKILL.md
# Then use Edit tool to update specific sections
```

## Deleting a Skill

```bash
rm -r hermes_data/learned-skills/<name>
```

## Guidelines for Good Skills

1. **Specific trigger**: Clearly describe WHEN to use the skill
2. **Self-contained**: Include all context needed — don't assume prior knowledge
3. **Actionable steps**: Numbered, concrete steps — not vague guidance
4. **Tool-aware**: List which tools (Bash, Write, Edit, etc.) the skill needs
5. **Tested**: Only save patterns that actually worked
6. **Concise**: Keep under 2000 characters — skills should be quick to scan

## Arguments

- `$0` — Skill name (lowercase, hyphens, e.g., "api-scaffolder")
- `$1` — Action: create, list, refine, delete (default: create)
- `$ARGUMENTS` — Full description if creating
