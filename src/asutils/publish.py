"""Publish asutils to PyPI."""
import os
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


def run(
    cmd: list[str], cwd: Path | None = None, env: dict | None = None
) -> subprocess.CompletedProcess:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(cmd, check=True, cwd=cwd, env=run_env)


def get_pypi_token() -> str | None:
    """Get PyPI API token from environment or shell config."""
    # Check if already in environment
    token = os.environ.get("PYPI_API_KEY")
    if token:
        return token

    # Try sourcing zshrc/bashrc to get it
    for rc_file in ["~/.zshrc", "~/.bashrc"]:
        rc_path = Path(rc_file).expanduser()
        if rc_path.exists():
            try:
                result = subprocess.run(
                    f"source {rc_path} 2>/dev/null && echo $PYPI_API_KEY",
                    shell=True,
                    capture_output=True,
                    text=True,
                    executable="/bin/zsh" if "zsh" in rc_file else "/bin/bash",
                )
                token = result.stdout.strip()
                if token:
                    return token
            except Exception:
                continue
    return None


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
    old_init = f'__version__ = "{__version__}"'
    new_init = f'__version__ = "{new_version}"'
    init_content = init_content.replace(old_init, new_init)
    init_file.write_text(init_content)

    # Update pyproject.toml
    pyproject_content = pyproject.read_text()
    old_pyproject = f'version = "{__version__}"'
    new_pyproject = f'version = "{new_version}"'
    pyproject_content = pyproject_content.replace(old_pyproject, new_pyproject)
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
    token = get_pypi_token()
    if not token:
        rprint("[red]No PyPI token found. Set PYPI_API_KEY in environment or ~/.zshrc[/]")
        raise typer.Exit(1)

    twine_env = {"TWINE_USERNAME": "__token__", "TWINE_PASSWORD": token}
    run([sys.executable, "-m", "twine", "upload", "dist/*"], cwd=root, env=twine_env)
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

    token = get_pypi_token()
    if not token:
        rprint("[red]No PyPI token found. Set PYPI_API_KEY in environment or ~/.zshrc[/]")
        raise typer.Exit(1)

    twine_env = {"TWINE_USERNAME": "__token__", "TWINE_PASSWORD": token}
    run([
        sys.executable, "-m", "twine", "upload",
        "--repository", "testpypi",
        "dist/*"
    ], cwd=root, env=twine_env)
    rprint("\n[bold green]✓ Published to TestPyPI[/]")
    rprint("Install with: pip install -i https://test.pypi.org/simple/ asutils")


if __name__ == "__main__":
    app()
