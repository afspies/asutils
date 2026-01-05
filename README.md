# asutils

Personal CLI utilities.

## Install

```bash
pip install asutils
```

## Commands

| Command | Description |
|---------|-------------|
| `asutils repo init [name]` | Scaffold new Python project |
| `asutils git sync` | Quick add, commit, push |
| `asutils publish release` | Publish to PyPI |
| `asutils claude skill list` | List bundled & installed Claude Code skills |
| `asutils claude skill add <name>` | Add a skill to `~/.claude/skills/` |
| `asutils claude skill add --profile=all` | Add all bundled skills |
| `asutils claude skill remove <name>` | Remove a skill |

## Dev Install

```bash
git clone https://github.com/afspies/asutils
cd asutils
uv pip install -e ".[dev]"
```

## License
MIT
