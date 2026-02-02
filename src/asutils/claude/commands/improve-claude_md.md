---
description: Set up CLAUDE.md with workflow orchestration patterns for plan mode, subagents, self-improvement, and task management.
---

# Improve CLAUDE.md

Set up or enhance the project's CLAUDE.md with proven workflow orchestration patterns. Also creates supporting files for lessons learned and task tracking.

## Instructions

When this command is invoked, perform the following steps:

### Step 1: Analyze Current State

Check what exists:
- Read `CLAUDE.md` if present (preserve existing project-specific content)
- Check for `.claude/lessons.md`
- Check for `.claude/tasks/todo.md`
- Scan for existing lessons in `docs/`, `agent.md`, or other documentation

### Step 2: Update or Create CLAUDE.md

Add/merge the following workflow orchestration section into CLAUDE.md. **Preserve existing project-specific content.**

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `.claude/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff your behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

### 7. Task Management
1. **Plan First**: Write plan to `.claude/tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `.claude/tasks/todo.md`
6. **Capture Lessons**: Update `.claude/lessons.md` after corrections

### Core Principles
- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

---

### Step 3: Create or Update Lessons File

Create `.claude/lessons.md` if it doesn't exist:

```markdown
# Lessons Learned

Insights, corrections, and patterns from development sessions.
Update this file after receiving corrections or discovering important patterns.

## Format

- **Date**: YYYY-MM-DD
- **Context**: What was being done
- **Learning**: What was discovered
- **Application**: How to apply going forward

---

## Lessons

<!-- Add lessons below -->
```

If the file exists, preserve existing lessons.

**Extract existing lessons** from:
- `docs/` markdown files mentioning patterns or guidelines
- Existing CLAUDE.md content about conventions
- Any `agent.md` or similar files

### Step 4: Create Task Tracking Structure

Create `.claude/tasks/todo.md`:

```markdown
# Task Tracking

## Active Tasks

<!-- Add active tasks here -->

## Completed

<!-- Move completed tasks here with notes -->
```

**Extract existing tasks** from:
- TODO comments in code (summarize key ones)
- Existing task lists in documentation
- Known work items in CLAUDE.md or README

### Step 5: Report Summary

After completing setup, report:
- Files created/updated
- Number of existing lessons extracted
- Tasks discovered
- Next steps for the user
