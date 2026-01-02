# asutils — Personal CLI Toolkit

A PyPI-hostable Python package consolidating personal dev utilities as CLI commands.

## Project Structure

```
asutils/
├── pyproject.toml
├── README.md
├── LICENSE                 # MIT
├── .gitignore
├── AGENTS.md               # For AI agents working on this repo
├── src/
│   └── asutils/
│       ├── __init__.py     # version, common utils
│       ├── cli.py          # main entry point (optional umbrella CLI)
│       ├── repo.py         # setup-new-repo command
│       ├── publish.py      # self-publish to PyPI
│       └── git.py          # git helpers (placeholder for future)
└── tests/
    ├── __init__.py
    └── test_repo.py
```

## pyproject.toml

```toml
[project]
name = "asutils"
version = "0.1.0"
description = "Personal CLI utilities"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
authors = [{ name = "Your Name", email = "you@example.com" }]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.1.0",
    "build>=1.0.0",
    "twine>=4.0.0",
]

[project.scripts]
as-repo = "asutils.repo:app"
as-publish = "asutils.publish:app"
as-git = "asutils.git:app"
# Umbrella command (all subcommands under one)
asutils = "asutils.cli:app"

[project.urls]
Repository = "https://github.com/YOURUSER/asutils"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/asutils"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "UP"]
```

## src/asutils/__init__.py

```python
__version__ = "0.1.0"
```

## src/asutils/cli.py

Umbrella CLI that groups all commands:

```python
import typer
from asutils import repo, publish, git

app = typer.Typer(name="asutils", help="Personal dev utilities")
app.add_typer(repo.app, name="repo")
app.add_typer(publish.app, name="publish")
app.add_typer(git.app, name="git")

if __name__ == "__main__":
    app()
```

## src/asutils/repo.py

```python
"""Setup new project repositories."""
import subprocess
from pathlib import Path
import typer
from rich import print as rprint

app = typer.Typer(help="Repository scaffolding")

GITIGNORE_TEMPLATE = """\
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.venv/
venv/
env/
*.egg-info/
dist/
build/
.eggs/

# ML/DL
*.pt
*.pth
*.ckpt
*.safetensors
wandb/
outputs/
logs/
lightning_logs/

# Data
data/
*.csv
*.parquet

# Env & IDE
.env
.env.local
.DS_Store
.idea/
.vscode/
*.swp
"""

AGENTS_TEMPLATE = """\
# AGENTS.md

## Project Context
This is a Python project managed with uv.

## Tools
- Use `bd` for task tracking
- Use `uv run` to execute scripts
- Use `uv add` to add dependencies

## Conventions
- Code in `src/`
- Tests in `tests/`
- Run `ruff check .` before committing
"""


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check)


@app.command("init")
def init(
    name: str = typer.Argument(".", help="Project name or '.' for current dir"),
    with_bd: bool = typer.Option(True, "--bd/--no-bd", help="Initialize bd task tracking"),
):
    """Scaffold a new Python repo with uv, git, and agent config."""
    
    path = Path(name)
    if name != ".":
        path.mkdir(parents=True, exist_ok=True)
    
    import os
    os.chdir(path)
    
    # Git
    if not Path(".git").exists():
        run(["git", "init"])
        rprint("[green]✓[/] git init")
    
    # uv
    if not Path("pyproject.toml").exists():
        run(["uv", "init", "--bare"])
        rprint("[green]✓[/] uv init")
    
    # .gitignore
    gitignore = Path(".gitignore")
    gitignore.write_text(GITIGNORE_TEMPLATE)
    rprint("[green]✓[/] .gitignore")
    
    # AGENTS.md
    agents = Path("AGENTS.md")
    agents.write_text(AGENTS_TEMPLATE)
    
    # bd init
    if with_bd:
        result = run(["bd", "init"], check=False)
        if result.returncode == 0:
            rprint("[green]✓[/] bd init")
        else:
            rprint("[yellow]![/] bd not available, skipping")
    
    rprint(f"\n[bold green]✓ Repo ready:[/] {Path.cwd()}")


if __name__ == "__main__":
    app()
```

## src/asutils/publish.py

```python
"""Publish asutils to PyPI."""
import subprocess
import sys
from pathlib import Path
import typer
from rich import print as rprint
from rich.prompt import Confirm

from asutils import __version__

app = typer.Typer(help="Package publishing utilities")


def get_package_root() -> Path:
    """Find the asutils package root (where pyproject.toml lives)."""
    # This file is at src/asutils/publish.py, so go up 3 levels
    return Path(__file__).parent.parent.parent


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, cwd=cwd)


@app.command("bump")
def bump(
    part: str = typer.Argument("patch", help="Version part: major, minor, patch"),
):
    """Bump version in __init__.py and pyproject.toml."""
    root = get_package_root()
    init_file = root / "src" / "asutils" / "__init__.py"
    pyproject = root / "pyproject.toml"
    
    # Parse current version
    major, minor, patch = map(int, __version__.split("."))
    
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    elif part == "patch":
        patch += 1
    else:
        rprint(f"[red]Unknown part:[/] {part}")
        raise typer.Exit(1)
    
    new_version = f"{major}.{minor}.{patch}"
    
    # Update __init__.py
    init_content = init_file.read_text()
    init_content = init_content.replace(f'__version__ = "{__version__}"', f'__version__ = "{new_version}"')
    init_file.write_text(init_content)
    
    # Update pyproject.toml
    pyproject_content = pyproject.read_text()
    pyproject_content = pyproject_content.replace(f'version = "{__version__}"', f'version = "{new_version}"')
    pyproject.write_text(pyproject_content)
    
    rprint(f"[green]✓[/] Bumped version: {__version__} → {new_version}")


@app.command("release")
def release(
    skip_tests: bool = typer.Option(False, "--skip-tests", help="Skip running tests"),
    skip_confirm: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
):
    """Build and publish to PyPI."""
    root = get_package_root()
    
    rprint(f"[bold]Publishing asutils v{__version__}[/]")
    
    # Run tests
    if not skip_tests:
        rprint("\n[bold]Running tests...[/]")
        result = subprocess.run([sys.executable, "-m", "pytest"], cwd=root)
        if result.returncode != 0:
            rprint("[red]Tests failed. Aborting.[/]")
            raise typer.Exit(1)
        rprint("[green]✓[/] Tests passed")
    
    # Confirm
    if not skip_confirm:
        if not Confirm.ask(f"\nPublish v{__version__} to PyPI?"):
            raise typer.Exit(0)
    
    # Clean old builds
    dist = root / "dist"
    if dist.exists():
        import shutil
        shutil.rmtree(dist)
    
    # Build
    rprint("\n[bold]Building...[/]")
    run([sys.executable, "-m", "build"], cwd=root)
    rprint("[green]✓[/] Build complete")
    
    # Upload
    rprint("\n[bold]Uploading to PyPI...[/]")
    run([sys.executable, "-m", "twine", "upload", "dist/*"], cwd=root)
    rprint(f"\n[bold green]✓ Published asutils v{__version__} to PyPI[/]")
    
    # Git tag
    run(["git", "tag", f"v{__version__}"], cwd=root)
    run(["git", "push", "--tags"], cwd=root)
    rprint(f"[green]✓[/] Tagged v{__version__}")


@app.command("test-pypi")
def test_pypi(
    skip_confirm: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
):
    """Publish to TestPyPI first."""
    root = get_package_root()
    
    if not skip_confirm:
        if not Confirm.ask(f"Publish v{__version__} to TestPyPI?"):
            raise typer.Exit(0)
    
    dist = root / "dist"
    if dist.exists():
        import shutil
        shutil.rmtree(dist)
    
    run([sys.executable, "-m", "build"], cwd=root)
    run([
        sys.executable, "-m", "twine", "upload",
        "--repository", "testpypi",
        "dist/*"
    ], cwd=root)
    rprint(f"\n[bold green]✓ Published to TestPyPI[/]")
    rprint(f"Install with: pip install -i https://test.pypi.org/simple/ asutils")


if __name__ == "__main__":
    app()
```

## src/asutils/git.py

```python
"""Git utilities (placeholder for expansion)."""
import subprocess
import typer
from rich import print as rprint

app = typer.Typer(help="Git helpers")


@app.command("sync")
def sync(message: str = typer.Option("sync", "-m", help="Commit message")):
    """Quick add, commit, push."""
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)
    rprint("[green]✓[/] Synced")


@app.command("undo")
def undo():
    """Undo last commit, keep changes staged."""
    subprocess.run(["git", "reset", "--soft", "HEAD~1"], check=True)
    rprint("[green]✓[/] Undid last commit")


if __name__ == "__main__":
    app()
```

## .gitignore

```
__pycache__/
*.py[cod]
*.so
.venv/
*.egg-info/
dist/
build/
.eggs/
.env
.DS_Store
.ruff_cache/
.pytest_cache/
```

## AGENTS.md

```markdown
# AGENTS.md

## Overview
`asutils` is a personal CLI toolkit published to PyPI.

## Commands
- `as-repo init [name]` — scaffold new Python repo
- `as-publish bump [major|minor|patch]` — bump version
- `as-publish release` — build and publish to PyPI
- `as-git sync` — quick commit and push

## Development
```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
ruff check .
```

## Publishing
```bash
as-publish bump patch
as-publish test-pypi      # test first
as-publish release        # real release
```

## PyPI Setup Required
1. Create account at pypi.org
2. Create API token at https://pypi.org/manage/account/token/
3. Configure `~/.pypirc`:
   ```
   [pypi]
   username = __token__
   password = pypi-YOUR-TOKEN-HERE
   
   [testpypi]
   username = __token__
   password = pypi-YOUR-TEST-TOKEN-HERE
   ```
```

## README.md

```markdown
# asutils

Personal CLI utilities.

## Install

```bash
pip install asutils
```

## Commands

| Command | Description |
|---------|-------------|
| `as-repo init [name]` | Scaffold new Python project |
| `as-git sync` | Quick add, commit, push |
| `as-publish release` | Publish to PyPI |

## Dev Install

```bash
git clone https://github.com/YOURUSER/asutils
cd asutils
uv pip install -e ".[dev]"
```

## License
MIT
```

## tests/test_repo.py

```python
from pathlib import Path
import tempfile
import os

def test_gitignore_template():
    from asutils.repo import GITIGNORE_TEMPLATE
    assert "__pycache__/" in GITIGNORE_TEMPLATE
    assert ".venv/" in GITIGNORE_TEMPLATE

def test_agents_template():
    from asutils.repo import AGENTS_TEMPLATE
    assert "bd" in AGENTS_TEMPLATE
```

---

## Implementation Notes for Claude Code

1. **Create the full structure above**
2. **Replace `YOURUSER` and email** with actual values (or leave as placeholders with a note)
3. **Test locally** with `uv pip install -e ".[dev]"` then run `as-repo --help`
4. **Ensure all commands work** before considering PyPI publish
5. **The publish command finds its own package root** so it works from anywhere

## Future Expansion Ideas
- `as-env` — manage .env files
- `as-docker` — common docker commands
- `as-ml` — ML experiment helpers (wandb init, etc.)
- `as-ssh` — SSH config helpers