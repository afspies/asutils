---
description: Toggle text-to-speech for Claude's responses
---

# Toggle TTS Mode

First, run this command to toggle TTS state:

```bash
asutils claude tts toggle
```

Based on the result:
- If **ENABLED**: TTS is now active. From now on, wrap spoken summaries in `<speak>...</speak>` tags. Keep spoken content concise. Code and technical details go outside tags.
- If **DISABLED**: TTS is off. Stop using `<speak>` tags.

Respond with a brief confirmation.
