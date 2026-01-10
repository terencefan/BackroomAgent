---
name: git-committer
description: Validates and executes Git operations with Conventional Commits standards. Use this skill when saving work, checkpointing changes, or finishing a task.
---

# Git Committer Skill

This skill defines the protocol for version control operations within the agent's workflow. It ensures that every significant code change is properly summarized, categorized, and committed to the repository, enabling safe rollback capability.

## When to Use This Skill

- **Post-Task Completion**: Immediately after successfully editing files to fulfill a user request.
- **Checkpointing**: In the middle of a complex multi-step refactor.
- **Agent Self-Correction**: When the user explicitly asks to "save" or "commit".

## Commit Message Standard (Conventional Commits)

All commit messages MUST follow this format:

```text
<type>(<scope>): <subject>

<body>
```

### 1. Header (`<type>(<scope>): <subject>`)
- **Types**:
    - `feat`: New feature for the user, not a new feature for build script.
    - `fix`: Bug fix for the user, not a fix to a build script.
    - `docs`: Documentation only changes.
    - `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc).
    - `refactor`: A code change that neither fixes a bug nor adds a feature.
    - `perf`: A code change that improves performance.
    - `test`: Adding missing tests or correcting existing tests.
    - `chore`: Changes to the build process or auxiliary tools and libraries such as documentation generation.
- **Scope** (Optional): A noun describing the section of the codebase (e.g., `logger`, `graph`, `frontend`).
- **Subject**: Short summary, imperative mood ("add logging" not "added logging"). No capital first letter, no dot at end.

### 2. Body
- Detailed summary of what changed.
- Bullet points are encouraged for multiple files/logical changes.

## Execution Protocol

1.  **Stage Changes**: Always use `git add .` to stage all modifications unless user specifies partial commit.
2.  **Generate Message**: Analyze the `git diff --staged` or the list of edited files to create the message.
3.  **Commit**: Execute `git commit -m "..."`. 
    - *Tip*: For multi-line commit messages in terminal tools, use a single line string with `\n` or multiple `-m` flags if supported, OR better yet:
    - Use `git commit -m "header" -m "body line 1" -m "body line 2"` to ensure clean formatting.

## Examples

### Good Commit
```bash
git commit -m "feat(utils): implement production logger" -m "- Add logger.py with dual-channel output" -m "- Replace all print statements with logger calls" -m "- Add logger-generator skill"
```

### Bad Commit
- `git commit -m "update code"` (Too vague)
- `git commit -m "Fixed bug"` (What bug?)
