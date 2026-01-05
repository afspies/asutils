# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## asutils Commands

This project provides CLI utilities via `asutils` (or standalone `as-*` commands):

```bash
# Development
asutils repo init [name]       # Scaffold new Python project
asutils git sync               # Quick add, commit, push
asutils publish bump [patch|minor|major]  # Bump version
asutils publish release        # Test, build, upload to PyPI, tag

# Claude Code skills
asutils claude skill list      # List bundled & installed skills
asutils claude skill add <name>           # Add skill to ~/.claude/skills/
asutils claude skill add --profile=all    # Add all bundled skills
asutils claude skill remove <name>        # Remove a skill
```

Run with `uv run asutils <command>` during development.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

Use 'bd' for task tracking
