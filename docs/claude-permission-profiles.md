# Claude Code Permission Profiles

A profile-based permission system for Claude Code using hooks and environment variables.

## Overview

This system enables easy switching between permission profiles without editing config files. Simply set an environment variable to select your desired permission level.

## Directory Structure

```
~/.claude/
├── settings.json                 # Hook configuration
├── profiles/
│   ├── default.yaml              # Restrictive (normal mode)
│   ├── dev.yaml                  # Development work
│   ├── yolo.yaml                 # Allow almost everything
│   └── readonly.yaml             # Only read operations
└── hooks/
    └── permission-router.py      # Decision engine
```

## Usage

```bash
claude                            # Uses 'default' profile
CLAUDE_PROFILE=dev claude         # Uses 'dev' profile
CLAUDE_PROFILE=yolo claude        # Uses 'yolo' profile

# Convenient aliases (add to .zshrc/.bashrc)
alias claude-dev='CLAUDE_PROFILE=dev claude'
alias claude-yolo='CLAUDE_PROFILE=yolo claude'
```

## Profile Schema (YAML)

### Development Profile

```yaml
# ~/.claude/profiles/dev.yaml
name: dev
description: Permissive profile for active development

# Rules evaluated in order - first match wins
rules:
  # Always deny dangerous operations (even in dev mode)
  - tool: Bash
    action: deny
    match:
      command:
        - "rm -rf /*"
        - "rm -rf /"
        - "sudo rm -rf *"
        - "> /dev/sd*"
        - "dd if=* of=/dev/*"
        - "mkfs.*"

  # Allow common dev commands
  - tool: Bash
    action: allow
    match:
      command:
        - "npm *"
        - "yarn *"
        - "pnpm *"
        - "git *"
        - "make *"
        - "cargo *"
        - "python *"
        - "python3 *"
        - "node *"
        - "go *"
        - "pytest *"
        - "jest *"

  # Allow filesystem inspection
  - tool: Bash
    action: allow
    match:
      command:
        - "ls *"
        - "find *"
        - "du *"
        - "df *"
        - "tree *"
        - "wc *"
        - "stat *"

  # Allow file operations in working directory
  - tool: Write
    action: allow
    match:
      path:
        - "./**"

  - tool: Edit
    action: allow
    match:
      path:
        - "./**"

# Unmatched requests fall through to Claude's normal prompting
default: passthrough
```

### YOLO Profile

```yaml
# ~/.claude/profiles/yolo.yaml
name: yolo
description: Allow everything except catastrophic operations

rules:
  # Still deny truly dangerous stuff
  - tool: Bash
    action: deny
    match:
      command:
        - "rm -rf /*"
        - "rm -rf /"
        - "sudo rm -rf *"

  # Allow everything else
  - tool: Bash
    action: allow
    match:
      command: ["*"]

  - tool: Write
    action: allow
    match:
      path: ["*"]

  - tool: Edit
    action: allow
    match:
      path: ["*"]

  - tool: WebFetch
    action: allow

default: allow
```

### Default Profile

```yaml
# ~/.claude/profiles/default.yaml
name: default
description: Conservative - defer to Claude's built-in prompts

# No allow rules - everything goes to normal permission flow
rules: []

default: passthrough
```

### Read-Only Profile

```yaml
# ~/.claude/profiles/readonly.yaml
name: readonly
description: Only allow read operations

rules:
  # Deny all writes
  - tool: Write
    action: deny
    match:
      path: ["*"]

  - tool: Edit
    action: deny
    match:
      path: ["*"]

  # Allow read-only bash commands
  - tool: Bash
    action: allow
    match:
      command:
        - "ls *"
        - "cat *"
        - "head *"
        - "tail *"
        - "find *"
        - "grep *"
        - "rg *"
        - "tree *"
        - "git status*"
        - "git log*"
        - "git diff*"
        - "git show*"

  # Deny other bash commands
  - tool: Bash
    action: deny
    match:
      command: ["*"]

default: passthrough
```

## Hook Script

```python
#!/usr/bin/env python3
"""
Permission Router - Profile-based permission decisions for Claude Code

Usage: Set CLAUDE_PROFILE=<profile_name> before launching claude
"""

import sys
import os
import json
import fnmatch
from pathlib import Path

try:
    import yaml
except ImportError:
    # Fallback if PyYAML not installed - passthrough everything
    print(json.dumps({"decision": {"behavior": "passthrough"}}))
    sys.exit(0)

PROFILES_DIR = Path.home() / ".claude" / "profiles"
LOG_FILE = Path.home() / ".claude" / "permission-router.log"
DEBUG = os.environ.get("CLAUDE_PROFILE_DEBUG", "0") == "1"


def log(msg: str):
    if DEBUG:
        with open(LOG_FILE, "a") as f:
            f.write(f"{msg}\n")


def load_profile(name: str) -> dict:
    for ext in (".yaml", ".yml", ".json"):
        path = PROFILES_DIR / f"{name}{ext}"
        if path.exists():
            with open(path) as f:
                if ext == ".json":
                    return json.load(f)
                return yaml.safe_load(f)
    return {"rules": [], "default": "passthrough"}


def matches(value: str, patterns: list) -> bool:
    if not patterns:
        return True
    return any(fnmatch.fnmatch(value, p) for p in patterns)


def evaluate(profile: dict, tool: str, input_data: dict) -> str:
    for rule in profile.get("rules", []):
        if rule.get("tool") != tool:
            continue

        match_spec = rule.get("match", {})

        # Check command patterns for Bash
        if tool == "Bash" and "command" in match_spec:
            cmd = input_data.get("command", "")
            if not matches(cmd, match_spec["command"]):
                continue

        # Check path patterns for file operations
        if tool in ("Write", "Edit", "Read") and "path" in match_spec:
            path = input_data.get("file_path", "")
            if not matches(path, match_spec["path"]):
                continue

        return rule.get("action", "passthrough")

    return profile.get("default", "passthrough")


def main():
    try:
        request = json.load(sys.stdin)
        tool = request.get("tool", "")
        input_data = request.get("input", {})

        profile_name = os.environ.get("CLAUDE_PROFILE", "default")
        profile = load_profile(profile_name)

        decision = evaluate(profile, tool, input_data)

        log(f"[{profile_name}] {tool}: {input_data} -> {decision}")

        print(json.dumps({"decision": {"behavior": decision}}))

    except Exception as e:
        log(f"ERROR: {e}")
        # On error, passthrough to normal behavior
        print(json.dumps({"decision": {"behavior": "passthrough"}}))


if __name__ == "__main__":
    main()
```

## Settings Configuration

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "type": "command",
        "command": "python3 ~/.claude/hooks/permission-router.py"
      }
    ]
  }
}
```

## Installation

### Manual Installation

```bash
# Create directories
mkdir -p ~/.claude/profiles ~/.claude/hooks

# Copy the hook script
cp permission-router.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/permission-router.py

# Copy profile files
cp profiles/*.yaml ~/.claude/profiles/

# Ensure PyYAML is installed
pip install pyyaml

# Update ~/.claude/settings.json to include the hook configuration
```

### Installation Script

```bash
#!/bin/bash
# install-permission-profiles.sh

set -e

CLAUDE_DIR="$HOME/.claude"
PROFILES_DIR="$CLAUDE_DIR/profiles"
HOOKS_DIR="$CLAUDE_DIR/hooks"

echo "Installing Claude Permission Profiles..."

# Create directories
mkdir -p "$PROFILES_DIR" "$HOOKS_DIR"

# Check for PyYAML
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "Installing PyYAML..."
    pip3 install pyyaml
fi

echo "Created directories:"
echo "  $PROFILES_DIR"
echo "  $HOOKS_DIR"

echo ""
echo "Next steps:"
echo "  1. Copy permission-router.py to $HOOKS_DIR/"
echo "  2. Copy profile YAML files to $PROFILES_DIR/"
echo "  3. Add hook configuration to ~/.claude/settings.json"
echo ""
echo "Usage:"
echo "  claude                     # default profile"
echo "  CLAUDE_PROFILE=dev claude  # dev profile"
echo "  CLAUDE_PROFILE=yolo claude # yolo profile"
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **YAML profiles** | Human-readable, easy to edit, supports comments |
| **First-match-wins** | Predictable, allows deny rules to override allows |
| **Glob patterns** | Familiar syntax, covers most use cases |
| **Passthrough default** | Safe fallback - unknown requests get normal prompts |
| **Safety denies first** | Even "yolo" mode blocks catastrophic commands |
| **Debug logging** | `CLAUDE_PROFILE_DEBUG=1` for troubleshooting |
| **Graceful degradation** | Missing PyYAML or errors → passthrough |

## Debugging

Enable debug logging to see permission decisions:

```bash
CLAUDE_PROFILE_DEBUG=1 CLAUDE_PROFILE=dev claude
```

Log file: `~/.claude/permission-router.log`

## Future Enhancements

1. **Profile inheritance**: `extends: default` to layer profiles
2. **Regex patterns**: For complex matching (opt-in with `regex:` prefix)
3. **CWD-aware rules**: Allow more in `~/Developer/*` than elsewhere
4. **CLI commands**: `claude profile list/switch` to manage profiles
5. **Profile validation**: Warn on malformed rules
6. **Time-based rules**: More permissive during work hours
7. **Project-specific overrides**: `.claude/profile-override.yaml` in project root
