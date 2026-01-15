---
description: Toggle text-to-speech for Claude's responses
allowed-tools: Bash(touch:*), Bash(rm:*), Bash(test:*)
---

# Toggle TTS Mode

First, let me check and toggle the TTS session state:

```bash
SESSION_FLAG="/tmp/claude-tts-$CLAUDE_SESSION_ID"
if [ -f "$SESSION_FLAG" ]; then
    rm "$SESSION_FLAG"
    echo "TTS_STATUS=disabled"
else
    touch "$SESSION_FLAG"
    echo "TTS_STATUS=enabled"
fi
```

Based on the result above:
- If TTS was **enabled**: Acknowledge that TTS is now active. From now on, wrap spoken summaries in `<speak>...</speak>` tags. Keep spoken content concise and conversational. Code, file paths, and technical details go outside the tags.
- If TTS was **disabled**: Acknowledge that TTS is now off. You no longer need to use `<speak>` tags.

Respond briefly confirming the new TTS state.
