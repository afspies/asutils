"""Text-to-speech engine using macOS say command."""

import re
import subprocess


def speak(text: str, voice: str = "Samantha", rate: int = 175) -> None:
    """Speak text using macOS say command.

    Args:
        text: Text to speak
        voice: macOS voice name (see `say -v ?` for list)
        rate: Words per minute (default ~175)
    """
    if not text.strip():
        return

    subprocess.run(
        ["say", "-v", voice, "-r", str(rate), text],
        check=False,
    )


def extract_spoken_text(content: str) -> str:
    """Extract text meant to be spoken from Claude's response.

    Looks for <speak>...</speak> tags first. If none found,
    falls back to stripping code blocks and returning the rest.

    Args:
        content: Claude's response text

    Returns:
        Text suitable for TTS
    """
    # Try <speak> tags first
    matches = re.findall(r"<speak>(.*?)</speak>", content, re.DOTALL)
    if matches:
        return " ".join(m.strip() for m in matches)

    # Fallback: strip code blocks and inline code
    text = content

    # Remove fenced code blocks (```...```)
    text = re.sub(r"```[\s\S]*?```", "", text)

    # Remove inline code (`...`)
    text = re.sub(r"`[^`]+`", "", text)

    # Remove markdown headers
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

    # Remove bullet points but keep text
    text = re.sub(r"^[\s]*[-*]\s+", "", text, flags=re.MULTILINE)

    # Remove numbered lists but keep text
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def list_voices() -> list[str]:
    """List available macOS voices.

    Returns:
        List of voice names
    """
    result = subprocess.run(
        ["say", "-v", "?"],
        capture_output=True,
        text=True,
        check=False,
    )

    voices = []
    for line in result.stdout.strip().split("\n"):
        if line:
            # Format: "Voice Name    language  # description"
            parts = line.split()
            if parts:
                # Voice name can be multi-word, ends before language code
                # e.g., "Samantha    en_US  # ..." or "Karen (Premium)  en_AU  # ..."
                voice_parts = []
                for part in parts:
                    if re.match(r"^[a-z]{2}[-_][A-Z]{2}", part):
                        break
                    if part == "#":
                        break
                    voice_parts.append(part)
                if voice_parts:
                    voices.append(" ".join(voice_parts))

    return voices


def focus_terminal(app: str = "auto") -> None:
    """Focus the terminal window using AppleScript.

    Args:
        app: Terminal app name ("auto", "Terminal", "iTerm", or "none")
    """
    if app == "none":
        return

    if app == "auto":
        app = detect_terminal()

    if app:
        subprocess.run(
            ["osascript", "-e", f'tell application "{app}" to activate'],
            check=False,
            capture_output=True,
        )


def detect_terminal() -> str | None:
    """Detect which terminal app is running.

    Returns:
        "iTerm" or "Terminal" or None
    """
    # Check for iTerm first (more common for power users)
    result = subprocess.run(
        ["pgrep", "-x", "iTerm2"],
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return "iTerm"

    result = subprocess.run(
        ["pgrep", "-x", "Terminal"],
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return "Terminal"

    return None
