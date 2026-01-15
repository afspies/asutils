---
name: tts
description: Enable text-to-speech for Claude's responses in this session
---

# TTS Mode Activated

Text-to-speech is now enabled for this session. Your spoken responses will be read aloud using macOS text-to-speech.

## How to Format Your Responses

When TTS mode is active, wrap content meant to be spoken aloud in `<speak>` tags:

```
<speak>Your conversational summary here.</speak>
```

**Guidelines:**
- Keep spoken content concise and conversational
- Code, file paths, technical commands, and implementation details go OUTSIDE the tags
- The `<speak>` tags will be stripped before the text is spoken
- If you forget the tags, your full response (minus code blocks) will be spoken

## Example Response Format

Here's an example showing the correct format:

---

I've implemented the authentication middleware. Here's the code:

```python
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not validate_token(token):
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    return await call_next(request)
```

<speak>I've added authentication middleware that checks for a valid token in the Authorization header. Requests without valid tokens get a 401 unauthorized response. The middleware runs on every HTTP request before it reaches your route handlers.</speak>

---

## Session State

This enables TTS for the current session only. The hook will read your responses aloud after each turn completes.

To enable TTS for all sessions, the user can run:
```bash
asutils claude tts enable --always
```
