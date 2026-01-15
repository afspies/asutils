---
description: Toggle text-to-speech for Claude's responses
---

# Toggle TTS Mode

TTS state: !`if [ -f /tmp/claude-tts-active ]; then rm /tmp/claude-tts-active && echo "DISABLED"; else touch /tmp/claude-tts-active && echo "ENABLED"; fi`

Based on the result above:
- If **ENABLED**: TTS is now active. From now on, wrap spoken summaries in `<speak>...</speak>` tags. Keep spoken content concise. Code and technical details go outside tags.
- If **DISABLED**: TTS is off. Stop using `<speak>` tags.

Respond with a brief confirmation.
