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
