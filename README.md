# asutils

Personal CLI utilities with a focus on Claude Code integration.

## Install

```bash
pip install asutils
```

## Quick Start: Claude Code Setup

One command to configure Claude Code with permissions, skills, and agents:

```bash
asutils claude setup
```

This installs:
- Permission profiles (auto-approve common dev operations)
- Bundled skills (reference docs for hooks, TTS, etc.)
- Bundled agents (code-review)

## Commands

### General Utilities

| Command | Description |
|---------|-------------|
| `asutils repo init [name]` | Scaffold new Python project |
| `asutils git sync` | Quick add, commit, push |
| `asutils publish bump <major\|minor\|patch>` | Bump version |
| `asutils publish release` | Build and publish to PyPI |

### Claude Code: Skills

Skills are markdown files that Claude Code loads as context when invoked.

| Command | Description |
|---------|-------------|
| `asutils claude skill list` | List bundled & installed skills |
| `asutils claude skill add <name>` | Install a skill to `~/.claude/skills/` |
| `asutils claude skill add --bundle=all` | Install all bundled skills |
| `asutils claude skill remove <name>` | Remove an installed skill |
| `asutils claude skill show <name>` | View skill content |

**Bundled Skills:**
- `claude-hooks` - Reference for creating Claude Code hooks

**Epic Skills Bundle** (for Epic Games employees):
- `epic/jira` - JIRA issue management for Epic's Atlassian Cloud
- `epic/confluence` - Confluence search via asutils CLI

Install with: `asutils claude skill add --bundle epic`

### Claude Code: Permission Profiles

Permission profiles auto-approve tool calls matching defined rules, reducing permission prompts.

| Command | Description |
|---------|-------------|
| `asutils claude permission install` | Install profiles and hook |
| `asutils claude permission list` | List available profiles |
| `asutils claude permission default <name>` | Set default profile |
| `asutils claude permission status` | Show current configuration |
| `asutils claude permission uninstall` | Remove profiles and hook |

**Bundled Profiles:**
- `default` - Conservative, passthrough everything
- `dev` - Auto-approve common dev tools (git, npm, pytest, etc.)
- `readonly` - Only allow read operations
- `yolo` - Allow everything except destructive operations

**Usage:**
```bash
# Use dev profile (auto-approves common operations)
asutils claude permission default dev

# Override per-session
CLAUDE_PROFILE=readonly claude
```

### Claude Code: Agents

Agents are specialized subagents with defined tools and prompts.

| Command | Description |
|---------|-------------|
| `asutils claude agent list` | List bundled & installed agents |
| `asutils claude agent add <name>` | Install an agent |
| `asutils claude agent add --all` | Install all bundled agents |
| `asutils claude agent remove <name>` | Remove an agent |
| `asutils claude agent show <name>` | View agent definition |

**Bundled Agents:**
- `code-review` - Review code for bugs, security issues, and quality

### Claude Code: Text-to-Speech (TTS)

Read Claude's responses aloud using macOS text-to-speech.

| Command | Description |
|---------|-------------|
| `asutils claude tts install` | Install TTS hooks |
| `asutils claude tts enable --always` | Enable for all sessions |
| `asutils claude tts disable` | Disable persistent TTS |
| `asutils claude tts status` | Show TTS configuration |
| `asutils claude tts test "Hello"` | Test TTS output |
| `asutils claude tts voices` | List available macOS voices |
| `asutils claude tts config` | Configure voice, rate, etc. |
| `asutils claude tts uninstall` | Remove TTS hooks |

**Usage:**
```bash
# Install hooks
asutils claude tts install

# Enable for all sessions
asutils claude tts enable --always

# Or toggle per-session in Claude Code
/tts

# Configure voice and speed
asutils claude tts config --voice "Alex" --rate 200
```

**How TTS Works:**
1. The `/tts` command toggles TTS mode and instructs Claude to use `<speak>` tags
2. A Stop hook fires after each response and extracts spoken content
3. Text is read aloud using macOS `say` command
4. Terminal window is focused (configurable)

**Configuration (`~/.claude/tts-config.yaml`):**
```yaml
voice: Samantha        # macOS voice name
rate: 175              # Words per minute
focus_window: true     # Focus terminal after speaking
terminal_app: auto     # auto | Terminal | iTerm | none
always_enabled: false  # Persistent mode
```

### Confluence Search (Epic Games)

Search Epic's internal Confluence wiki directly from the command line.

| Command | Description |
|---------|-------------|
| `asutils confluence search "query"` | Search for pages |
| `asutils confluence search "q1" "q2" --parallel` | Multi-query parallel search |
| `asutils confluence page <id>` | Get page content (markdown) |
| `asutils confluence spaces` | List available spaces |
| `asutils confluence cql 'text~"term"'` | Raw CQL search |
| `asutils confluence children <id>` | Get child pages |

**Prerequisites:**
- Set `JIRA_API_TOKEN` environment variable (same token works for Confluence)
- Run `asutils epic setup` to configure

**Usage:**
```bash
# Search across all Confluence
asutils confluence search "deployment process"

# Parallel search with multiple queries
asutils confluence search "authentication" "OAuth" "SSO" --parallel

# Get full page content
asutils confluence page 12345678

# Search within a specific space
asutils confluence search "API" --space DEV
```

### Epic Setup

One-command setup for Epic Games integrations.

| Command | Description |
|---------|-------------|
| `asutils epic setup` | Configure Epic integrations and install skills |
| `asutils epic status` | Show integration status |
| `asutils epic verify` | Test Confluence authentication |

**Usage:**
```bash
# Full setup (creates config, verifies auth, installs skills)
asutils epic setup

# Check status
asutils epic status
```

## Development

```bash
git clone https://github.com/afspies/asutils
cd asutils
uv pip install -e ".[dev]"
```

## License

MIT
