#!/usr/bin/env python3
"""TTS Stop hook - Speaks Claude's response when TTS is enabled.

This hook fires when Claude finishes responding (Stop event).
It checks if TTS is enabled for the session or globally, extracts
the spoken text from Claude's response, and reads it aloud.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Configuration paths
CLAUDE_DIR = Path.home() / ".claude"
TTS_CONFIG_FILE = CLAUDE_DIR / "tts-config.yaml"


def load_config() -> dict:
    """Load TTS configuration."""
    config = {
        "voice": "Samantha",
        "rate": 175,
        "focus_window": True,
        "terminal_app": "auto",
        "always_enabled": False,
    }

    if TTS_CONFIG_FILE.exists():
        try:
            import yaml

            with open(TTS_CONFIG_FILE) as f:
                user_config = yaml.safe_load(f) or {}
                config.update(user_config)
        except Exception:
            pass

    return config


def is_tts_enabled(session_id: str, config: dict) -> bool:
    """Check if TTS is enabled for this session or globally."""
    # Check persistent/always enabled
    if config.get("always_enabled", False):
        return True

    # Check TTS active flag (shared across sessions)
    tts_flag = Path(tempfile.gettempdir()) / "claude-tts-active"
    return tts_flag.exists()


def get_last_assistant_message(transcript_path: str) -> str | None:
    """Extract the last assistant message from the transcript."""
    try:
        with open(transcript_path) as f:
            lines = f.readlines()

        # Transcript is JSONL - each line is a JSON object
        # Look for the last assistant message
        last_message = None

        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)

                # Handle different transcript formats
                # Format 1: {"type": "assistant", "message": {...}}
                if entry.get("type") == "assistant":
                    message = entry.get("message", {})
                    content = message.get("content", [])
                    if isinstance(content, list):
                        # Content is array of blocks
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                            elif isinstance(block, str):
                                text_parts.append(block)
                        if text_parts:
                            last_message = "\n".join(text_parts)
                            break
                    elif isinstance(content, str):
                        last_message = content
                        break

                # Format 2: {"role": "assistant", "content": "..."}
                if entry.get("role") == "assistant":
                    content = entry.get("content", "")
                    if isinstance(content, str) and content:
                        last_message = content
                        break
                    if isinstance(content, list):
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                        if text_parts:
                            last_message = "\n".join(text_parts)
                            break

            except json.JSONDecodeError:
                continue

        return last_message

    except Exception:
        return None


def main():
    """Main hook entry point."""
    try:
        # Read hook input from stdin
        request = json.load(sys.stdin)
        session_id = request.get("session_id", "")
        transcript_path = request.get("transcript_path", "")

        # Load config
        config = load_config()

        # Check if TTS is enabled
        if not is_tts_enabled(session_id, config):
            # TTS not enabled, exit silently
            print(json.dumps({}))
            sys.exit(0)

        # Get last assistant message
        if not transcript_path:
            print(json.dumps({}))
            sys.exit(0)

        message = get_last_assistant_message(transcript_path)
        if not message:
            print(json.dumps({}))
            sys.exit(0)

        # Import speak functions (avoid import at top for faster startup when disabled)
        from asutils.claude.tts.speak import (
            extract_spoken_text,
            focus_terminal,
            speak,
        )

        # Extract text to speak
        text = extract_spoken_text(message)
        if not text:
            print(json.dumps({}))
            sys.exit(0)

        # Speak the text
        speak(text, voice=config.get("voice", "Samantha"), rate=config.get("rate", 175))

        # Focus terminal window if configured
        if config.get("focus_window", True):
            focus_terminal(config.get("terminal_app", "auto"))

        # Output empty JSON (hook completed successfully)
        print(json.dumps({}))

    except Exception as e:
        # Log error but don't block Claude
        log_file = CLAUDE_DIR / "tts-hook.log"
        try:
            with open(log_file, "a") as f:
                f.write(f"ERROR: {e}\n")
        except Exception:
            pass
        print(json.dumps({}))


if __name__ == "__main__":
    main()
