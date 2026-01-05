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

# Predefined profiles
PROFILES: dict[str, list[str]] = {
    "minimal": ["permission-allowances"],
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


def get_profile_skills(profile: str) -> list[str]:
    """Get list of skill names for a profile."""
    if profile == "all":
        return list(get_bundled_skills().keys())
    return PROFILES.get(profile, [])


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


@app.command("install")
def install_skill(
    name: Annotated[str | None, typer.Argument(help="Skill name to install")] = None,
    profile: Annotated[
        str | None, typer.Option("--profile", "-p", help="Install skills from profile")
    ] = None,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing skills")
    ] = False,
):
    """Install a skill to Claude Code's skills directory."""
    if name is None and profile is None:
        rprint("[red]Provide either a skill name or --profile[/red]")
        raise typer.Exit(1)

    bundled = get_bundled_skills()
    installed = get_installed_skills()

    # Determine which skills to install
    if profile:
        skills_to_install = get_profile_skills(profile)
        if not skills_to_install:
            rprint(f"[red]Unknown profile: {profile}[/red]")
            rprint(f"[dim]Available profiles: {', '.join(PROFILES.keys())}[/dim]")
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
        rprint(f"[green]Installed '{skill_name}' to {target}[/green]")


@app.command("uninstall")
def uninstall_skill(
    name: Annotated[str | None, typer.Argument(help="Skill name to uninstall")] = None,
    profile: Annotated[
        str | None, typer.Option("--profile", "-p", help="Uninstall skills from profile")
    ] = None,
    all_skills: Annotated[
        bool, typer.Option("--all", help="Uninstall all skills")
    ] = False,
):
    """Uninstall a skill from Claude Code's skills directory."""
    if name is None and profile is None and not all_skills:
        rprint("[red]Provide a skill name, --profile, or --all[/red]")
        raise typer.Exit(1)

    installed = get_installed_skills()

    if all_skills:
        skills_to_remove = list(installed.keys())
    elif profile:
        skills_to_remove = [s for s in get_profile_skills(profile) if s in installed]
    else:
        skills_to_remove = [name] if name in installed else []

    if not skills_to_remove:
        rprint("[yellow]No matching skills to uninstall[/yellow]")
        return

    for skill_name in skills_to_remove:
        path = installed[skill_name]
        path.unlink()
        rprint(f"[green]Uninstalled '{skill_name}' from {path}[/green]")


@app.command("profiles")
def list_profiles():
    """List available skill profiles."""
    console = Console()
    table = Table(title="Skill Profiles")
    table.add_column("Profile", style="cyan")
    table.add_column("Skills")

    for profile_name in PROFILES:
        skills = get_profile_skills(profile_name)
        table.add_row(profile_name, ", ".join(skills) or "(all bundled)")

    console.print(table)


if __name__ == "__main__":
    app()
