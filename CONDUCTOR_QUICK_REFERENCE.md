# Conductor + Epic Gateway - Quick Reference

## Quick Setup (5 minutes)

### 1. Get API Key
Visit: https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/getting-started
- Navigate to "Claude Code PoC" workspace
- Copy/generate API key

### 2. Configure Conductor
Open Conductor → Settings → Env, add:

```bash
ANTHROPIC_BASE_URL=https://live.ai.epicgames.com
ANTHROPIC_AUTH_TOKEN=test
ANTHROPIC_CUSTOM_HEADERS=x-portkey-api-key: YOUR_API_KEY_HERE
x-portkey-debug: true
x-vertex-ai-llm-request-type: shared
```

**Note**: Do NOT include `x-portkey-config` header. Your API key has a default config in Portkey.

### 3. Restart & Test
- Restart Conductor
- Create new workspace
- Test with simple query

## Environment Variables Reference

| Variable | Value | Purpose |
|----------|-------|---------|
| `ANTHROPIC_BASE_URL` | `https://live.ai.epicgames.com` | Gateway endpoint |
| `ANTHROPIC_AUTH_TOKEN` | `test` | Placeholder auth |
| `ANTHROPIC_CUSTOM_HEADERS` | (see below) | Auth + config headers |

### Custom Headers Format

Each header on a new line:
```
x-portkey-api-key: YOUR_KEY
x-portkey-debug: true
x-vertex-ai-llm-request-type: shared
```

**Do NOT include** `x-portkey-config` - your API key has a default config.

## Available Environments

| Name | Config ID | Use Case |
|------|-----------|----------|
| **Live** | `pc-claude-60f174` | Production (recommended) |
| Live Test | `pc-claude-750f48` | Config testing |
| Dev | `pc-claude-8ae240` | Development |

## Troubleshooting Quick Fixes

### Auth Failed
- [ ] Check API key is correct (no extra spaces)
- [ ] Verify key permissions in Portkey
- [ ] Try regenerating key

### Connection Timeout
- [ ] Test: `curl -I https://live.ai.epicgames.com`
- [ ] Check VPN connection
- [ ] Review Console.app logs

### Headers Not Sent
- [ ] Verify newline format in `ANTHROPIC_CUSTOM_HEADERS`
- [ ] Check Claude Code version compatibility
- [ ] Try alternative format: `key1:value1,key2:value2`

## Verification Commands

```bash
# Test gateway connectivity
curl -I https://live.ai.epicgames.com

# Check Conductor logs
# Open Console.app → Filter: "Conductor"

# Verify environment in Claude Code
echo $ANTHROPIC_BASE_URL
```

## Quick Links

- **Portkey Dashboard**: https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/
- **Conductor Docs**: https://docs.conductor.build/
- **Gateway Repo**: https://github.ol.epicgames.net/ai-gateway/claude-gateway
- **Support**: Slack #ts-ai-gateway-support

## Security Reminders

- ✅ Keep API key secure
- ✅ Don't commit to git
- ✅ Use VPN if required
- ✅ Rotate keys periodically
- ✅ Monitor usage in Portkey dashboard

## Testing Checklist

Quick verification:
1. ✅ API key from Portkey
2. ✅ Env vars set in Conductor
3. ✅ Conductor restarted
4. ✅ New workspace created
5. ✅ Claude responds
6. ✅ No auth errors

---

**Last Updated**: 2026-01-29 | **Version**: 1.0
