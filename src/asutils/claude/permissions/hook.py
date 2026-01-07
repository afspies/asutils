#!/usr/bin/env python3
"""
Permission Router - Profile-based permission decisions for Claude Code

Usage: Set CLAUDE_PROFILE=<profile_name> before launching claude
       Or set default with: asutils claude permission default <profile_name>

Profiles are stored in ~/.claude/profiles/
"""

import fnmatch
import json
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    # Fallback if PyYAML not installed - passthrough everything
    print(json.dumps({"decision": {"behavior": "passthrough"}}))
    sys.exit(0)

PROFILES_DIR = Path.home() / ".claude" / "profiles"
DEFAULT_PROFILE_FILE = Path.home() / ".claude" / "default-profile"
LOG_FILE = Path.home() / ".claude" / "permission-router.log"
DEBUG = os.environ.get("CLAUDE_PROFILE_DEBUG", "0") == "1"


def log(msg: str):
    if DEBUG:
        with open(LOG_FILE, "a") as f:
            f.write(f"{msg}\n")


def get_default_profile() -> str:
    """Get the default profile name from file or return 'default'."""
    if DEFAULT_PROFILE_FILE.exists():
        content = DEFAULT_PROFILE_FILE.read_text().strip()
        if content:
            return content
    return "default"


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
        # PermissionRequest uses tool_name and tool_input fields
        tool = request.get("tool_name", "")
        input_data = request.get("tool_input", {})

        profile_name = os.environ.get("CLAUDE_PROFILE") or get_default_profile()
        profile = load_profile(profile_name)

        decision = evaluate(profile, tool, input_data)

        log(f"[{profile_name}] {tool}: {input_data} -> {decision}")

        # Output format for PermissionRequest hooks
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {
                    "behavior": decision
                }
            }
        }
        print(json.dumps(output))

    except Exception as e:
        log(f"ERROR: {e}")
        # On error, passthrough to normal behavior
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {
                    "behavior": "passthrough"
                }
            }
        }
        print(json.dumps(output))


if __name__ == "__main__":
    main()
