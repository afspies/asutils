# Conductor Configuration for Epic Claude Gateway

This guide explains how to configure Conductor to use the Epic AI Gateway (Portkey) for Claude Code requests.

## Overview

Conductor is a Mac app that runs multiple Claude Code instances in parallel. By default, it connects directly to Anthropic's API, but it can be configured to use Epic's internal AI gateway through environment variables.

## Prerequisites

1. **Portkey API Key**: You need an API key from the "Claude Code PoC" workspace
   - Visit: https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/getting-started
   - Generate or copy an existing API key
   - Keep this key secure - you'll need it for configuration

2. **Conductor App**: Download and install from https://www.conductor.build/

## Configuration Steps

### Step 1: Open Conductor Settings

1. Launch the Conductor app
2. Click on **Conductor** in the menu bar
3. Select **Settings** (or press `⌘,`)
4. Navigate to the **Env** tab

### Step 2: Configure Environment Variables

In the Env tab, add the following environment variables:

#### Required Variables

```bash
# Gateway endpoint
ANTHROPIC_BASE_URL=https://live.ai.epicgames.com

# Placeholder auth token (required by Claude Code)
ANTHROPIC_AUTH_TOKEN=test

# Custom headers for Portkey authentication
ANTHROPIC_CUSTOM_HEADERS=x-portkey-api-key: YOUR_PORTKEY_API_KEY_HERE
x-portkey-debug: true
x-vertex-ai-llm-request-type: shared
```

**Important Notes:**
- Replace `YOUR_PORTKEY_API_KEY_HERE` with your actual Portkey API key from Step 1
- The `ANTHROPIC_AUTH_TOKEN=test` is a placeholder - actual authentication happens via the custom headers
- **Do NOT include `x-portkey-config` header** - Your API key has a default config in Portkey and overriding it will cause errors
- Each header should be on a new line in the `ANTHROPIC_CUSTOM_HEADERS` value

#### Optional Variables

```bash
# Enable debug logging for troubleshooting
CLAUDE_DEBUG=true

# Disable telemetry (recommended for internal use)
DISABLE_TELEMETRY=true
```

### Step 3: Verify Configuration

1. **Save** the environment variable settings in Conductor
2. **Restart** Conductor for the changes to take effect
3. Create a new workspace and start a Claude Code session
4. Verify the connection by running a simple command like:
   ```
   What version are you?
   ```

### Step 4: Monitor Network Requests (Optional)

To verify that requests are going through the Epic gateway:

1. Open **Console.app** on your Mac
2. Filter for "Conductor" processes
3. Look for network requests going to `live.ai.epicgames.com`
4. Check that the custom headers are being included

## Environment Details

### Available Gateways

| Environment | URL | Portkey Config | Description |
|------------|-----|----------------|-------------|
| **Live** (Recommended) | `https://live.ai.epicgames.com` | `pc-claude-60f174` | Production environment for general use |
| Live Test | `https://live.ai.epicgames.com` | `pc-claude-750f48` | Test endpoint for verifying configs |
| Dev | `https://dev.ai.epicgames.com` | `pc-claude-8ae240` | Development environment |

**Note:** The Live environment (`pc-claude-60f174`) is recommended for normal use.

### Authentication Methods

The Epic Claude Gateway supports two authentication methods:

1. **API Key** (Recommended for Conductor)
   - Uses a static Portkey API key
   - No token expiration or refresh needed
   - Simpler configuration
   - Better for applications like Conductor

2. **SSO (Single Sign-On)**
   - OAuth2 authentication via Epic OKTA
   - Tokens expire and need refresh
   - Requires background token management
   - Better for CLI tools but complex for Conductor

## Troubleshooting

### Issue: "Authentication failed" or "Invalid API key"

**Solution:**
1. Verify your Portkey API key is correct
2. Check that the key has the necessary permissions in Portkey
3. Ensure there are no extra spaces or newlines in the API key value
4. Try regenerating the API key in Portkey

### Issue: Wrong model received (requested Opus, got Sonnet)

**Symptoms:**
- You set model to Opus in Conductor
- Portkey logs show Sonnet was used
- All models route to Sonnet regardless of request

**Cause:** Your API key is assigned to the wrong Portkey config (likely "Claude-Code" instead of "pc-claude-60f174")

**Solution:**
1. Go to Portkey Dashboard: https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/
2. Navigate to **API Keys** section
3. Find your API key (starts with the characters you see in your config)
4. Check the **assigned config** - it should be `pc-claude-60f174` (named "claude-code-both-live")
5. If it's different (e.g., "Claude-Code"), change it to `pc-claude-60f174`
6. Save changes
7. Restart Conductor and test again

**How to detect:** Run `./test-conductor-config.sh YOUR_API_KEY` - it will warn if routing is broken

### Issue: Requests timeout or fail to connect

**Solution:**
1. Verify you can reach the gateway URL from your network:
   ```bash
   curl -I https://live.ai.epicgames.com
   ```
2. Check if you're on Epic's VPN (may be required)
3. Review Conductor logs in Console.app for connection errors

### Issue: Custom headers not being sent

**Solution:**
1. Verify the format of `ANTHROPIC_CUSTOM_HEADERS` - each header should be on a new line
2. Try the alternative format with colon-separated pairs:
   ```bash
   ANTHROPIC_CUSTOM_HEADERS=x-portkey-config:pc-claude-60f174,x-portkey-api-key:YOUR_KEY,x-portkey-debug:true
   ```
3. Check Claude Code version compatibility - older versions may not support custom headers

### Issue: "ANTHROPIC_CUSTOM_HEADERS not supported"

**Fallback Option:**
If Claude Code doesn't support `ANTHROPIC_CUSTOM_HEADERS`, you can use a local proxy:

1. Create a simple HTTP proxy that adds the required headers
2. Run the proxy on localhost (e.g., `http://localhost:8080`)
3. Set `ANTHROPIC_BASE_URL=http://localhost:8080` in Conductor
4. The proxy forwards requests to `https://live.ai.epicgames.com` with headers added

See the **Alternative Approaches** section below for implementation details.

## Alternative Approaches

If the standard environment variable approach doesn't work, consider these alternatives:

### Option A: Local HTTP Proxy

Create a lightweight proxy server that:
- Listens on localhost (e.g., `http://localhost:8080`)
- Accepts standard Anthropic API requests
- Adds Portkey authentication headers automatically
- Forwards to Epic gateway (`https://live.ai.epicgames.com`)

**Configuration:**
```bash
ANTHROPIC_BASE_URL=http://localhost:8080
```

### Option B: Wrapper Script

Replace Conductor's bundled Claude executable with a wrapper:
- Location: `/Applications/Conductor.app/Contents/Resources/bin/claude`
- Wrapper sets environment variables and authentication headers
- Calls the original Claude Code executable

**Pros:** No proxy needed, works at the binary level
**Cons:** Requires modifying Conductor.app, may break with updates

### Option C: Direct Database Configuration

Modify Conductor's SQLite database directly:
- Path: `~/Library/Application Support/com.conductor.app/conductor.db`
- Update `settings` table with gateway configuration
- May allow setting custom headers that aren't available via UI

**Pros:** Persists across restarts, low-level control
**Cons:** Schema may change, requires reverse engineering

## Security Considerations

1. **API Key Protection**:
   - Keep your Portkey API key secure
   - Don't commit it to version control
   - Consider using environment variable files that are .gitignored

2. **Network Security**:
   - The gateway may require Epic VPN access
   - All traffic is encrypted via HTTPS
   - Authentication headers are sent securely

3. **Access Control**:
   - Portkey API keys can be scoped to specific workspaces
   - Monitor usage in the Portkey dashboard
   - Rotate keys periodically for security

## Resources

- [Conductor Documentation](https://docs.conductor.build/)
- [Conductor Environment Variables Guide](https://docs.conductor.build/tips/conductor-env.md)
- [Epic Claude Gateway Repository](https://github.ol.epicgames.net/ai-gateway/claude-gateway)
- [Portkey Dashboard](https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/)

## Support

For issues or questions:
- **Conductor Issues**: https://github.com/conductor-build/conductor/issues
- **Epic Gateway Issues**: Slack #ts-ai-gateway-support
- **Portkey Issues**: https://portkey.ai/docs

## Testing Checklist

Use this checklist to verify your configuration:

- [ ] Portkey API key obtained from workspace
- [ ] Environment variables set in Conductor Settings → Env
- [ ] `ANTHROPIC_BASE_URL` points to `https://live.ai.epicgames.com`
- [ ] `ANTHROPIC_CUSTOM_HEADERS` includes all required headers
- [ ] `ANTHROPIC_AUTH_TOKEN` set to `test`
- [ ] Conductor restarted after configuration changes
- [ ] New workspace created to test configuration
- [ ] Claude Code responds to basic queries
- [ ] Network requests go to Epic gateway (verified in Console.app)
- [ ] No authentication errors in logs

## Example Configuration

Here's a complete example of the Env configuration in Conductor:

```
ANTHROPIC_BASE_URL=https://live.ai.epicgames.com
ANTHROPIC_AUTH_TOKEN=test
ANTHROPIC_CUSTOM_HEADERS=x-portkey-api-key: pk-abc123-xyz789-example-key-do-not-use
x-portkey-debug: true
x-vertex-ai-llm-request-type: shared
DISABLE_TELEMETRY=true
```

**Remember:** Replace `pk-abc123-xyz789-example-key-do-not-use` with your actual API key!

**Note:** Do NOT include `x-portkey-config` header - your API key has a default config in Portkey.

## Version Compatibility

- **Conductor**: Tested with version 1.x.x
- **Claude Code**: Requires version with `ANTHROPIC_CUSTOM_HEADERS` support (1.x.x+)
- **Epic Gateway**: Live environment (`pc-claude-60f174`)
- **Last Updated**: 2026-01-29
