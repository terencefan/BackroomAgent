---
name: skill-creator
description: Generates new agent skills following the official Agent Skills specification. Use when you need to teach the AI a new capability, create reusable workflows, or document best practices in a structured format.
---

# Skill Creator Skill

This skill helps you generate, validate, and structure new capabilities (Skills) for the agent, ensuring strict adherence to the [Agent Skills Specification](https://agentskills.io/specification).

## When to Use This Skill

Use this skill when you want to:
- Create a new skill directory and `SKILL.md` file
- Convert a set of instructions or a prompt into a reusable skill
- Standardize existing documentation into the Skill format
- Validate that a skill follows naming and formatting rules

## Skill Generation Workflow

### 1. Planning

Before generating a skill, define:
*   **Name**: 1-64 chars, lowercase `a-z`, numbers, hyphens. No start/end hyphen. Match directory name.
*   **Purpose**: What specific task does it solve?
*   **Trigger**: When should the agent use it?
*   **Context**: What dependencies or tools does it need?

### 2. File Structure

Always create this structure:
```
.github/skills/
└── <skill-name>/
    └── SKILL.md          # Required: Frontmatter + Instructions
```

Optional subdirectories (only if needed):
- `scripts/` (executable code)
- `references/` (lookup tables, extended docs)
- `assets/` (templates, images)

### 3. Frontmatter Template

Every `SKILL.md` MUST start with this YAML block:

```yaml
---
name: skill-name-here      # REQUIRED: Matches directory, valid formatting
description: Description.  # REQUIRED: Max 1024 chars. What + When to use.
license: Apache-2.0        # OPTIONAL
compatibility: ...         # OPTIONAL: Environment requirements
---
```

### 4. Body Content Template

Use this structure for the Markdown body:

```markdown
# [Skill Name]

[Brief introduction]

## When to Use This Skill

- [Condition 1]
- [Condition 2]

## Step-by-Step Instructions

1. [Step 1]
2. [Step 2]

## Examples

#### Example 1: [Scenario]
[Description or input/output]

## Best Practices / Notes

- [Tip 1]
- [Tip 2]
```

## Naming Rules (Strict)

- ✅ `pdf-processing`, `data-analysis`, `code-review-v2`
- ❌ `PDF-Processing` (no uppercase)
- ❌ `-pdf` (no starting hyphen)
- ❌ `pdf--processing` (no consecutive hyphens)
- ❌ `pdf processing` (no spaces)

## Generation Prompts

When asking the agent to create a skill, provide:
1.  **Name**: "Create a skill named `git-bisect-helper`"
2.  **Goal**: "It should guide the helping user find bugs using git bisect"
3.  **Details**: "Include steps for starting, marking good/bad, and resetting"

## Validation Checklist

- [ ] Directory name matches exactly `name` in frontmatter
- [ ] Frontmatter is valid YAML
- [ ] Description explains "What" and "When"
- [ ] References to files use relative paths (e.g., `scripts/run.py`)
- [ ] Main `SKILL.md` is concise (progressive disclosure)

