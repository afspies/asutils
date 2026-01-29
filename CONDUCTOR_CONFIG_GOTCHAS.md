# Conductor Configuration Gotchas

This document covers common issues when configuring Conductor with Epic Claude Gateway.

## Issue #1: x-portkey-config Header Should NOT Be Used

### Problem
Including `x-portkey-config: pc-claude-60f174` in `ANTHROPIC_CUSTOM_HEADERS` causes:
```
HTTP 400: "Cannot override default config set for this API key"
```

### Why
Portkey API keys have a **default config** assigned to them. When you try to override it with `x-portkey-config` header, Portkey rejects the request.

### Solution
**Remove** the `x-portkey-config` header entirely:

```bash
# ✗ WRONG - includes x-portkey-config
ANTHROPIC_CUSTOM_HEADERS=x-portkey-config: pc-claude-60f174
x-portkey-api-key: YOUR_KEY
x-portkey-debug: true
x-vertex-ai-llm-request-type: shared

# ✓ CORRECT - no x-portkey-config
ANTHROPIC_CUSTOM_HEADERS=x-portkey-api-key: YOUR_KEY
x-portkey-debug: true
x-vertex-ai-llm-request-type: shared
```

## Issue #2: Wrong Portkey Config Assignment

### Problem
You request `claude-opus-4` in Conductor, but Portkey uses `claude-sonnet-4` instead. All models route to Sonnet.

### Why
Your API key is assigned to the wrong Portkey config (likely "Claude-Code" or similar) instead of `pc-claude-60f174`.

The "Claude-Code" config either:
- Has no model-based routing
- Always routes to Sonnet
- Has different routing rules

### Expected Behavior
The `pc-claude-60f174` config has proper conditional routing:
```json
{
  "strategy": {
    "mode": "conditional",
    "conditions": [
      {"query": {"params.model": {"$regex": "haiku"}}, "then": "haiku"},
      {"query": {"params.model": {"$regex": "sonnet"}}, "then": "sonnet"},
      {"query": {"params.model": {"$regex": "opus"}}, "then": "opus"}
    ],
    "default": "sonnet"
  }
}
```

This means:
- `claude-opus-4` → Routes to Opus backend
- `claude-sonnet-4` → Routes to Sonnet backend
- `claude-haiku-4` → Routes to Haiku backend
- Anything else → Defaults to Sonnet

### Solution

**Step 1**: Verify the issue
```bash
./test-conductor-config.sh YOUR_API_KEY
```

If you see this warning:
```
⚠ WARNING: Config Routing Issue Detected!
  You requested Opus but got Sonnet
```

Then your config is wrong.

**Step 2**: Fix in Portkey Dashboard

1. Go to: https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/
2. Navigate to **API Keys** section
3. Find your API key (search by the first 10 characters)
4. Check the **Assigned Config** field
5. If it says "Claude-Code" or anything other than `pc-claude-60f174`:
   - Click **Edit**
   - Change **Assigned Config** to: `pc-claude-60f174` (named "claude-code-both-live")
   - Save changes

**Step 3**: Verify the fix
```bash
./test-conductor-config.sh YOUR_API_KEY
```

Should now show:
```
✓ Model routing is working correctly!
```

**Step 4**: Restart Conductor
No changes needed in Conductor settings - just restart the app.

### How to Detect

Run the test script which requests `claude-opus-4`:
```bash
./test-conductor-config.sh YOUR_API_KEY
```

If it gets back a model containing "opus" → ✓ Routing works
If it gets back a model containing "sonnet" → ✗ Wrong config

## Issue #3: Model Name Format

### Problem
Not sure what model name to use in Conductor.

### Solution
Use standard Anthropic model names:
- `claude-opus-4` or `claude-opus-4-5` (same thing)
- `claude-sonnet-4` or `claude-sonnet-4-5` (same thing)
- `claude-haiku-4` or `claude-haiku-4-5` (same thing)

The Portkey config automatically maps these to backend-specific names:
- `claude-opus-4` → `@claude-codegen-poc/claude-opus-4-5-20251101`
- `claude-sonnet-4` → `@claude-codegen-poc/claude-sonnet-4-5-20250929`
- `claude-haiku-4` → `@claude-codegen-poc/claude-haiku-4-5-20251001`

**Don't** use the `@...` format directly - let Portkey handle the mapping.

## Complete Working Configuration

After fixing both issues above, your Conductor Settings → Env should be:

```bash
ANTHROPIC_BASE_URL=https://live.ai.epicgames.com
ANTHROPIC_AUTH_TOKEN=test
ANTHROPIC_CUSTOM_HEADERS=x-portkey-api-key: YOUR_API_KEY_HERE
x-portkey-debug: true
x-vertex-ai-llm-request-type: shared
```

And in Portkey Dashboard:
- API Key: `YOUR_API_KEY_HERE`
- Assigned Config: `pc-claude-60f174` (claude-code-both-live)

## Verification Checklist

- [ ] API key obtained from Portkey
- [ ] API key assigned to config `pc-claude-60f174` in Portkey Dashboard
- [ ] `x-portkey-config` header NOT included in Conductor env vars
- [ ] Run `./test-conductor-config.sh YOUR_KEY` - all checks pass
- [ ] Conductor restarted after configuration
- [ ] Test in Conductor with different models (Opus, Sonnet, Haiku)
- [ ] Verify correct model used in Portkey logs

## Debugging

### Check what config your API key uses

The API response headers include `x-portkey-provider` and other metadata, but not the config ID directly. The best way is to:

1. Check in Portkey Dashboard → API Keys
2. Or test with Opus request and see if you get Opus back

### Check Portkey logs

1. Go to Portkey Dashboard
2. Navigate to **Logs** section
3. Filter by your API key or time range
4. Check:
   - Requested model vs. actual model used
   - Config ID used for the request
   - Any errors or warnings

### Enable debug mode

The `x-portkey-debug: true` header enables detailed logging in Portkey. Check the Portkey logs for:
- Routing decisions
- Config application
- Backend selection
- Fallback attempts

## Related Files

- `CONDUCTOR_SETUP.md` - Complete setup guide
- `CONDUCTOR_QUICK_REFERENCE.md` - Quick reference card
- `CONDUCTOR_README.md` - Overview and introduction
- `test-conductor-config.sh` - Automated config testing
- `verify-conductor-gateway.sh` - Installation verification

## Support

- Portkey Dashboard: https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/
- Epic Gateway: Slack #ts-ai-gateway-support
- Conductor: https://github.com/conductor-build/conductor/issues

---

**Last Updated**: 2026-01-29 | **Version**: 1.1
