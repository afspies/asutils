# Conductor + Epic Claude Gateway

This directory contains configuration guides and tools for setting up Conductor to use the Epic AI Gateway.

## What is Conductor?

[Conductor](https://www.conductor.build/) is a Mac application that enables running multiple Claude Code instances in parallel. It provides a unified interface for managing multiple AI-powered coding sessions simultaneously.

## What is Epic Claude Gateway?

The Epic Claude Gateway is an internal proxy that routes Claude Code requests through Epic's AI infrastructure (powered by Portkey). It provides:

- **Cost Management**: Centralized billing and usage tracking
- **Access Control**: Managed authentication and permissions
- **Analytics**: Usage metrics and monitoring
- **Security**: Internal routing and audit logging

## Documentation

### 📖 Full Setup Guide
**[CONDUCTOR_SETUP.md](CONDUCTOR_SETUP.md)** - Complete step-by-step configuration guide
- Prerequisites and requirements
- Detailed configuration steps
- Environment variable reference
- Troubleshooting common issues
- Alternative approaches
- Security considerations

### ⚡ Quick Reference
**[CONDUCTOR_QUICK_REFERENCE.md](CONDUCTOR_QUICK_REFERENCE.md)** - One-page reference card
- 5-minute setup instructions
- Essential environment variables
- Quick troubleshooting guide
- Verification checklist
- Key links and resources

### 🔧 Verification Script
**[verify-conductor-gateway.sh](verify-conductor-gateway.sh)** - Automated configuration checker
```bash
./verify-conductor-gateway.sh
```

Checks:
- Conductor installation
- Gateway connectivity
- Database configuration
- API key validation
- Environment setup

## Quick Start

### 1. Get Portkey API Key

Visit the Portkey dashboard:
```
https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/getting-started
```

Navigate to the "Claude Code PoC" workspace and copy/generate an API key.

### 2. Configure Conductor

Open **Conductor → Settings → Env** and add:

```bash
ANTHROPIC_BASE_URL=https://live.ai.epicgames.com
ANTHROPIC_AUTH_TOKEN=test
ANTHROPIC_CUSTOM_HEADERS=x-portkey-api-key: YOUR_API_KEY_HERE
x-portkey-debug: true
x-vertex-ai-llm-request-type: shared
```

Replace `YOUR_API_KEY_HERE` with your actual API key.

**Important**: Do NOT include `x-portkey-config` header - your API key has a default Portkey config.

### 3. Restart and Test

1. Restart Conductor
2. Create a new workspace
3. Test with a simple query: "What version are you?"

### 4. Verify Configuration

Run the verification script:
```bash
./verify-conductor-gateway.sh
```

## Environment Variables Explained

| Variable | Value | Purpose |
|----------|-------|---------|
| `ANTHROPIC_BASE_URL` | `https://live.ai.epicgames.com` | Routes requests to Epic gateway instead of Anthropic API |
| `ANTHROPIC_AUTH_TOKEN` | `test` | Placeholder auth token (actual auth via custom headers) |
| `ANTHROPIC_CUSTOM_HEADERS` | (multi-line value) | Portkey configuration and authentication headers |

### Custom Headers Breakdown

The `ANTHROPIC_CUSTOM_HEADERS` value should contain (each on a new line):

- `x-portkey-api-key: YOUR_KEY` - Your Portkey API key for authentication
- `x-portkey-debug: true` - Enables debug logging for troubleshooting
- `x-vertex-ai-llm-request-type: shared` - Required for backend routing

**Note**: Do NOT include `x-portkey-config` - your API key already has a default Portkey configuration

## Available Environments

| Environment | Gateway URL | Portkey Config | Use Case |
|------------|-------------|----------------|----------|
| **Live (Recommended)** | `https://live.ai.epicgames.com` | `pc-claude-60f174` | Production use |
| Live Test | `https://live.ai.epicgames.com` | `pc-claude-750f48` | Testing new configs |
| Dev | `https://dev.ai.epicgames.com` | `pc-claude-8ae240` | Development testing |

To use a different environment, change both the `ANTHROPIC_BASE_URL` and the `x-portkey-config` header value.

## Troubleshooting

### Common Issues

**Authentication Failed**
- Verify API key is correct (no extra spaces)
- Check key permissions in Portkey dashboard
- Try regenerating the API key

**Wrong Model Used (Requested Opus, Got Sonnet)**
- **Cause**: API key assigned to wrong Portkey config
- **Symptom**: All models route to Sonnet regardless of request
- **Fix**: In Portkey Dashboard → API Keys, change assigned config to `pc-claude-60f174`
- **Detect**: Run `./test-conductor-config.sh YOUR_API_KEY` to check routing
- **Expected config**: `pc-claude-60f174` (named "claude-code-both-live")
- **Wrong configs**: "Claude-Code" or similar

**Cannot Connect to Gateway**
- Test connectivity: `curl -I https://live.ai.epicgames.com`
- Ensure you're on Epic VPN (if required)
- Check Console.app logs for Conductor

**Custom Headers Not Working**
- Verify newline format in `ANTHROPIC_CUSTOM_HEADERS`
- Check Claude Code version compatibility
- Try alternative header format: `key:value,key:value`

### Debug Mode

Enable additional logging by adding:
```bash
CLAUDE_DEBUG=true
```

Then check logs in Console.app (filter for "Conductor").

## Architecture

```
┌─────────────┐
│  Conductor  │
│    (Mac)    │
└──────┬──────┘
       │ ANTHROPIC_BASE_URL
       │ ANTHROPIC_CUSTOM_HEADERS
       ▼
┌─────────────────────┐
│  Epic AI Gateway    │
│  (Portkey)          │
│  live.ai.epicgames  │
└──────┬──────────────┘
       │ x-portkey-config
       │ x-portkey-api-key
       ▼
┌─────────────────────┐
│  Anthropic API      │
│  (Claude Models)    │
└─────────────────────┘
```

## Security

**API Key Protection:**
- Keep your Portkey API key secure
- Don't commit keys to version control
- Use environment variable files that are .gitignored
- Rotate keys periodically

**Network Security:**
- All traffic encrypted via HTTPS
- May require Epic VPN access
- Authentication headers sent securely

**Access Control:**
- Keys scoped to specific workspaces
- Monitor usage in Portkey dashboard
- Track sessions and costs

## Alternative Approaches

If the standard environment variable approach doesn't work, see the full setup guide for:

1. **Local HTTP Proxy** - Intercept and add headers via proxy
2. **Wrapper Script** - Replace Claude binary with wrapper
3. **Database Configuration** - Direct SQLite database modification

## Related Tools

### Claude Gateway CLI
The official Epic tool for running Claude Code with the gateway:
```bash
# Installation
npm install -g claude-gateway

# Usage
claude-gateway
```

Located at: `/Users/alex.spies/Developer/claude-gateway`

### Comparison: Conductor vs Claude Gateway CLI

| Feature | Conductor | Claude Gateway CLI |
|---------|-----------|-------------------|
| **Multiple Sessions** | ✅ Parallel workspaces | ❌ Single session |
| **GUI** | ✅ Native Mac app | ❌ Terminal only |
| **Gateway Support** | ⚙️ Manual config | ✅ Built-in |
| **Authentication** | 🔑 API Key only | ✅ SSO + API Key |
| **Token Refresh** | ❌ Static key | ✅ Auto-refresh |
| **Best For** | Multiple projects | Single project work |

## Resources

### Documentation
- [Conductor Official Docs](https://docs.conductor.build/)
- [Conductor Environment Variables](https://docs.conductor.build/tips/conductor-env.md)
- [Epic Gateway Repository](https://github.ol.epicgames.net/ai-gateway/claude-gateway)

### Dashboards
- [Portkey Dashboard](https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/)
- [Portkey API Keys](https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/getting-started)

### Support
- **Conductor Issues**: https://github.com/conductor-build/conductor/issues
- **Epic Gateway Support**: Slack #ts-ai-gateway-support
- **Portkey Documentation**: https://portkey.ai/docs

## Contributing

Found an issue or improvement? Please:
1. Test the fix in your environment
2. Update the relevant documentation
3. Submit a pull request or open an issue

## Version History

- **v1.0.0** (2026-01-29) - Initial release
  - Complete setup guide
  - Quick reference card
  - Verification script
  - Troubleshooting documentation

## License

Copyright Epic Games, Inc. All Rights Reserved.

---

**Last Updated**: 2026-01-29 | **Maintainer**: AI Gateway Team
