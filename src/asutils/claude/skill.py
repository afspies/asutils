"""Skill management for Claude Code."""

from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Manage Claude Code skills")

# Bundled skills directory (alongside this module)
BUNDLED_SKILLS_DIR = Path(__file__).parent / "skills"

# Claude Code skills directory
CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"

# Predefined bundles
BUNDLES: dict[str, list[str]] = {
    "minimal": [],  # Empty - use for essential skills only
    "default": [],  # All bundled skills - populated dynamically (same as "all")
    "dev": ["claude-hooks"],  # Development-focused skills
    "all": [],  # Populated dynamically with all available skills
}


def get_bundled_skills() -> dict[str, Path]:
    """Return dict of skill_name -> path for all bundled skills."""
    skills = {}
    if BUNDLED_SKILLS_DIR.exists():
        for f in BUNDLED_SKILLS_DIR.glob("*.md"):
            skills[f.stem] = f
    return skills


def get_installed_skills() -> dict[str, Path]:
    """Return dict of skill_name -> path for installed skills."""
    skills = {}
    if CLAUDE_SKILLS_DIR.exists():
        for f in CLAUDE_SKILLS_DIR.glob("*.md"):
            skills[f.stem] = f
    return skills


def get_bundle_skills(bundle: str) -> list[str]:
    """Get list of skill names for a bundle."""
    if bundle in ("all", "default"):
        return list(get_bundled_skills().keys())
    return BUNDLES.get(bundle, [])


@app.command("list")
def list_skills(
    bundled: Annotated[bool, typer.Option("--bundled", "-b", help="Show bundled skills")] = False,
    installed: Annotated[
        bool, typer.Option("--installed", "-i", help="Show installed skills")
    ] = False,
):
    """List available and installed skills."""
    # Default to showing both if neither specified
    if not bundled and not installed:
        bundled = installed = True

    console = Console()
    bundled_skills = get_bundled_skills()
    installed_skills = get_installed_skills()

    if bundled:
        table = Table(title="Bundled Skills")
        table.add_column("Name", style="cyan")
        table.add_column("Installed", style="green")
        table.add_column("Path")

        for name, path in sorted(bundled_skills.items()):
            is_installed = name in installed_skills
            table.add_row(name, "yes" if is_installed else "no", str(path))

        console.print(table)

    if installed:
        if bundled:
            console.print()  # Spacing between tables

        table = Table(title="Installed Skills")
        table.add_column("Name", style="cyan")
        table.add_column("Source", style="yellow")
        table.add_column("Path")

        for name, path in sorted(installed_skills.items()):
            source = "bundled" if name in bundled_skills else "custom"
            table.add_row(name, source, str(path))

        if not installed_skills:
            console.print("[dim]No skills installed[/dim]")
        else:
            console.print(table)


@app.command("show")
def show_skill(
    name: Annotated[str, typer.Argument(help="Skill name to show")],
    installed: Annotated[
        bool, typer.Option("--installed", "-i", help="Show installed version")
    ] = False,
):
    """Show the content of a skill."""
    if installed:
        skills = get_installed_skills()
        source = "installed"
    else:
        skills = get_bundled_skills()
        source = "bundled"

    if name not in skills:
        rprint(f"[red]Skill '{name}' not found in {source} skills[/red]")
        raise typer.Exit(1)

    path = skills[name]
    rprint(f"[dim]# {source}: {path}[/dim]\n")
    rprint(path.read_text())


@app.command("add")
def add_skill(
    name: Annotated[str | None, typer.Argument(help="Skill name to add")] = None,
    bundle: Annotated[
        str | None, typer.Option("--bundle", "-b", help="Add skills from bundle")
    ] = None,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing skills")
    ] = False,
):
    """Add a skill to Claude Code's skills directory."""
    if name is None and bundle is None:
        rprint("[red]Provide either a skill name or --bundle[/red]")
        raise typer.Exit(1)

    bundled = get_bundled_skills()
    installed = get_installed_skills()

    # Determine which skills to install
    if bundle:
        skills_to_install = get_bundle_skills(bundle)
        if not skills_to_install:
            rprint(f"[red]Unknown or empty bundle: {bundle}[/red]")
            rprint(f"[dim]Available bundles: {', '.join(BUNDLES.keys())}[/dim]")
            raise typer.Exit(1)
    else:
        skills_to_install = [name]

    # Ensure target directory exists
    CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    for skill_name in skills_to_install:
        if skill_name not in bundled:
            rprint(f"[red]Skill '{skill_name}' not found in bundled skills[/red]")
            continue

        target = CLAUDE_SKILLS_DIR / f"{skill_name}.md"

        if skill_name in installed and not force:
            rprint(f"[yellow]'{skill_name}' already installed (use --force to overwrite)[/yellow]")
            continue

        source = bundled[skill_name]
        target.write_text(source.read_text())
        rprint(f"[green]Added '{skill_name}' to {target}[/green]")


@app.command("remove")
def remove_skill(
    name: Annotated[str | None, typer.Argument(help="Skill name to remove")] = None,
    bundle: Annotated[
        str | None, typer.Option("--bundle", "-b", help="Remove skills from bundle")
    ] = None,
    all_skills: Annotated[
        bool, typer.Option("--all", help="Remove all skills")
    ] = False,
):
    """Remove a skill from Claude Code's skills directory."""
    if name is None and bundle is None and not all_skills:
        rprint("[red]Provide a skill name, --bundle, or --all[/red]")
        raise typer.Exit(1)

    installed = get_installed_skills()

    if all_skills:
        skills_to_remove = list(installed.keys())
    elif bundle:
        skills_to_remove = [s for s in get_bundle_skills(bundle) if s in installed]
    else:
        skills_to_remove = [name] if name in installed else []

    if not skills_to_remove:
        rprint("[yellow]No matching skills to remove[/yellow]")
        return

    for skill_name in skills_to_remove:
        path = installed[skill_name]
        path.unlink()
        rprint(f"[green]Removed '{skill_name}' from {path}[/green]")


@app.command("bundles")
def list_bundles():
    """List available skill bundles."""
    console = Console()
    table = Table(title="Skill Bundles")
    table.add_column("Bundle", style="cyan")
    table.add_column("Skills")

    for bundle_name in BUNDLES:
        skills = get_bundle_skills(bundle_name)
        if bundle_name == "all":
            display = ", ".join(skills) if skills else "(no bundled skills)"
        elif skills:
            display = ", ".join(skills)
        else:
            display = "(empty)"
        table.add_row(bundle_name, display)

    console.print(table)


if __name__ == "__main__":
    app()
