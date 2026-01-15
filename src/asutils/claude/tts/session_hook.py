#!/usr/bin/env python3
"""TTS UserPromptSubmit hook - Enables TTS when /tts command is detected.

This hook fires before processing user prompts. It checks if the user
typed /tts and creates a session flag file to enable TTS for this session.
"""

import json
import sys
import tempfile
from pathlib import Path


def main():
    """Main hook entry point."""
    try:
        # Read hook input from stdin
        request = json.load(sys.stdin)
        session_id = request.get("session_id", "")
        prompt = request.get("prompt", "")

        # Check if user is toggling TTS
        if prompt.strip().lower() == "/tts":
            session_flag = Path(tempfile.gettempdir()) / f"claude-tts-{session_id}"

            if session_flag.exists():
                # Disable TTS for this session
                session_flag.unlink()
                print(
                    json.dumps(
                        {
                            "systemMessage": "TTS disabled for this session. Your responses will no longer be read aloud."
                        }
                    )
                )
            else:
                # Enable TTS for this session
                session_flag.touch()
                print(
                    json.dumps(
                        {
                            "systemMessage": "TTS enabled for this session. Your responses will be read aloud. Use <speak>...</speak> tags to specify which parts should be spoken."
                        }
                    )
                )
        else:
            # Not a TTS command, passthrough
            print(json.dumps({}))

    except Exception as e:
        # Log error but don't block Claude
        log_file = Path.home() / ".claude" / "tts-hook.log"
        try:
            with open(log_file, "a") as f:
                f.write(f"SessionHook ERROR: {e}\n")
        except Exception:
            pass
        print(json.dumps({}))


if __name__ == "__main__":
    main()
