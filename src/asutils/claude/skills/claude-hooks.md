---
name: claude-hooks
description: Reference for creating and configuring Claude Code hooks. Use when setting up automation, permission control, or custom behaviors.
---

# Claude Code Hooks Reference

Quick reference for setting up hooks in Claude Code.

## Configuration Locations

- `~/.claude/settings.json` - User settings (global)
- `.claude/settings.json` - Project settings
- `.claude/settings.local.json` - Local project settings (not committed)

## Hook Format

**IMPORTANT**: The `matcher` field must be a **string**, not an object!

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here"
          }
        ]
      }
    ]
  }
}
```

### Matcher Patterns (strings only!)

- `"*"` - Match all tools
- `""` - Also matches all (empty string)
- `"Write"` - Exact match
- `"Edit|Write"` - Regex pattern
- `"Notebook.*"` - Regex wildcard

## Hook Events

| Event | Matcher? | Purpose |
|-------|----------|---------|
| `PreToolUse` | Yes | Before tool executes |
| `PermissionRequest` | Yes | When permission dialog shown |
| `PostToolUse` | Yes | After tool completes |
| `UserPromptSubmit` | No | Before prompt processed |
| `Stop` | No | When agent finishes |
| `SubagentStop` | No | When subagent finishes |
| `SessionStart` | No | Session begins |
| `SessionEnd` | No | Session ends |
| `PreCompact` | No | Before context compaction |
| `Notification` | Yes | When notifications sent |

## Common Tool Names for Matchers

- `Bash` - Shell commands
- `Read` - File reading
- `Write` - File writing
- `Edit` - File editing
- `Glob` - File pattern matching
- `Grep` - Content search
- `Task` - Subagent tasks
- `WebFetch`, `WebSearch` - Web operations
- `mcp__<server>__<tool>` - MCP tools

## Hook Input (via stdin)

Hooks receive JSON with:

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/directory",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": { ... }
}
```

## Hook Output

### Exit Codes

- **0**: Success (stdout shown in verbose mode)
- **2**: Blocking error (stderr fed back to Claude)
- **Other**: Non-blocking error (stderr shown to user)

### JSON Output (exit code 0)

For `PermissionRequest` hooks to auto-allow/deny:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow"
    }
  }
}
```

Or to deny with a message:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "deny",
      "message": "Reason for denial"
    }
  }
}
```

Or to passthrough (let Claude's normal prompting handle it):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "passthrough"
    }
  }
}
```

**IMPORTANT**: The hook reads `tool_name` and `tool_input` from stdin JSON (not `tool` or `input`).

## Example: Permission Router Hook

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/permission-router.py"
          }
        ]
      }
    ]
  }
}
```

## Environment Variables

- `CLAUDE_PROJECT_DIR` - Project root directory
- `CLAUDE_ENV_FILE` - (SessionStart only) File to persist env vars

## Debugging

1. Run `/hooks` in Claude Code to see registered hooks
2. Use `claude --debug` for detailed hook execution logs
3. Check hook script permissions (`chmod +x`)
4. Test commands manually first

## Common Mistakes

1. **Using object for matcher**: `"matcher": {}` is WRONG, use `"matcher": "*"`
2. **Missing hooks array**: Each matcher needs a `hooks` array with command objects
3. **Old format**: Don't use `{"type": "command", "command": "..."}` at top level
4. **Unescaped quotes**: Use `\"` inside JSON strings

## Quick Setup with asutils

```bash
# Install permission profiles system
asutils claude permission install

# Set default profile
asutils claude permission default dev

# Check status
asutils claude permission status
```
