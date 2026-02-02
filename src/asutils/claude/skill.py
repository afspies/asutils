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

# Bundled commands directory (slash commands, not Epic-specific)
BUNDLED_COMMANDS_DIR = Path(__file__).parent / "commands"

# Epic Games specific skills (optional, not installed by default)
EPIC_SKILLS_DIR = Path(__file__).parent / "skills" / "epic"

# Claude Code skills directory
CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"

# Claude Code commands directory (for skills that act as slash commands)
CLAUDE_COMMANDS_DIR = Path.home() / ".claude" / "commands"

# Predefined bundles
BUNDLES: dict[str, list[str]] = {
    "minimal": [],  # Empty - use for essential skills only
    "default": [],  # All bundled skills - populated dynamically (same as "all")
    "dev": ["claude-hooks"],  # Development-focused skills
    "all": [],  # Populated dynamically with all available skills
    "epic": [],  # Epic Games specific skills - populated from epic/ subdirectory
    "commands": [],  # Bundled slash commands - populated from commands/ subdirectory
}


def get_bundled_skills() -> dict[str, Path]:
    """Return dict of skill_name -> path for all bundled skills (excludes epic)."""
    skills = {}
    if BUNDLED_SKILLS_DIR.exists():
        for f in BUNDLED_SKILLS_DIR.glob("*.md"):
            skills[f.stem] = f
    return skills


def get_epic_skills() -> dict[str, Path]:
    """Return dict of skill_name -> path for Epic Games specific skills."""
    skills = {}
    if EPIC_SKILLS_DIR.exists():
        for f in EPIC_SKILLS_DIR.glob("*.md"):
            skills[f.stem] = f
    return skills


def get_bundled_commands() -> dict[str, Path]:
    """Return dict of command_name -> path for bundled commands (non-Epic)."""
    commands = {}
    if BUNDLED_COMMANDS_DIR.exists():
        for f in BUNDLED_COMMANDS_DIR.glob("*.md"):
            commands[f.stem] = f
    return commands


def get_all_available_skills() -> dict[str, Path]:
    """Return dict of all skills including epic and commands (prefixed with 'epic/' or 'commands/')."""
    skills = get_bundled_skills()
    for name, path in get_epic_skills().items():
        skills[f"epic/{name}"] = path
    for name, path in get_bundled_commands().items():
        skills[f"commands/{name}"] = path
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
    if bundle == "epic":
        return [f"epic/{name}" for name in get_epic_skills().keys()]
    if bundle == "commands":
        return [f"commands/{name}" for name in get_bundled_commands().keys()]
    return BUNDLES.get(bundle, [])


def get_installed_commands() -> dict[str, Path]:
    """Return dict of command_name -> path for installed commands."""
    commands = {}
    if CLAUDE_COMMANDS_DIR.exists():
        for f in CLAUDE_COMMANDS_DIR.glob("*.md"):
            commands[f.stem] = f
    return commands


@app.command("list")
def list_skills(
    bundled: Annotated[bool, typer.Option("--bundled", "-b", help="Show bundled skills")] = False,
    installed: Annotated[
        bool, typer.Option("--installed", "-i", help="Show installed skills")
    ] = False,
    epic: Annotated[bool, typer.Option("--epic", "-e", help="Show Epic Games skills")] = False,
    commands: Annotated[bool, typer.Option("--commands", "-c", help="Show bundled commands")] = False,
):
    """List available and installed skills."""
    # Default to showing all if none specified
    if not bundled and not installed and not epic and not commands:
        bundled = installed = epic = commands = True

    console = Console()
    bundled_skills = get_bundled_skills()
    bundled_cmds = get_bundled_commands()
    epic_skills = get_epic_skills()
    installed_skills = get_installed_skills()
    installed_commands = get_installed_commands()

    if bundled:
        table = Table(title="Bundled Skills")
        table.add_column("Name", style="cyan")
        table.add_column("Installed", style="green")
        table.add_column("Path")

        for name, path in sorted(bundled_skills.items()):
            is_installed = name in installed_skills
            table.add_row(name, "yes" if is_installed else "no", str(path))

        console.print(table)

    if epic:
        if bundled:
            console.print()

        table = Table(title="Epic Games Skills (use --bundle epic to install)")
        table.add_column("Name", style="magenta")
        table.add_column("Installed", style="green")
        table.add_column("Description")

        for name, path in sorted(epic_skills.items()):
            is_installed = name in installed_commands
            # Try to extract description from frontmatter
            content = path.read_text()
            desc = ""
            if content.startswith("---"):
                try:
                    import yaml
                    _, frontmatter, _ = content.split("---", 2)
                    meta = yaml.safe_load(frontmatter)
                    desc = meta.get("description", "")[:60]
                    if len(meta.get("description", "")) > 60:
                        desc += "..."
                except Exception:
                    pass
            table.add_row(f"epic/{name}", "yes" if is_installed else "no", desc)

        console.print(table)

    if commands:
        if bundled or epic:
            console.print()

        table = Table(title="Bundled Commands (use --bundle commands to install)")
        table.add_column("Name", style="blue")
        table.add_column("Installed", style="green")
        table.add_column("Description")

        for name, path in sorted(bundled_cmds.items()):
            is_installed = name in installed_commands
            # Try to extract description from frontmatter
            content = path.read_text()
            desc = ""
            if content.startswith("---"):
                try:
                    import yaml
                    _, frontmatter, _ = content.split("---", 2)
                    meta = yaml.safe_load(frontmatter)
                    desc = meta.get("description", "")[:60]
                    if len(meta.get("description", "")) > 60:
                        desc += "..."
                except Exception:
                    pass
            table.add_row(f"commands/{name}", "yes" if is_installed else "no", desc)

        console.print(table)

    if installed:
        if bundled or epic or commands:
            console.print()  # Spacing between tables

        table = Table(title="Installed Skills (~/.claude/skills/)")
        table.add_column("Name", style="cyan")
        table.add_column("Source", style="yellow")
        table.add_column("Path")

        for name, path in sorted(installed_skills.items()):
            source = "bundled" if name in bundled_skills else "custom"
            table.add_row(name, source, str(path))

        if not installed_skills:
            console.print("[dim]No skills installed in ~/.claude/skills/[/dim]")
        else:
            console.print(table)

        # Also show installed commands (epic skills)
        console.print()
        table = Table(title="Installed Commands (~/.claude/commands/)")
        table.add_column("Name", style="magenta")
        table.add_column("Source", style="yellow")
        table.add_column("Path")

        for name, path in sorted(installed_commands.items()):
            if name in epic_skills:
                source = "epic"
            elif name in bundled_cmds:
                source = "bundled"
            else:
                source = "custom"
            table.add_row(name, source, str(path))

        if not installed_commands:
            console.print("[dim]No commands installed in ~/.claude/commands/[/dim]")
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
    name: Annotated[str | None, typer.Argument(help="Skill name to add (use 'epic/name' or 'commands/name')")] = None,
    bundle: Annotated[
        str | None, typer.Option("--bundle", "-b", help="Add skills from bundle (e.g., 'epic', 'commands')")
    ] = None,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing skills")
    ] = False,
):
    """Add a skill to Claude Code's skills/commands directory.

    For Epic Games specific skills, use 'epic/skillname' or --bundle epic.
    For bundled commands, use 'commands/name' or --bundle commands.
    Both epic and commands are installed to ~/.claude/commands/ as slash commands.
    """
    if name is None and bundle is None:
        rprint("[red]Provide either a skill name or --bundle[/red]")
        raise typer.Exit(1)

    # Get all available skills (bundled + epic)
    all_skills = get_all_available_skills()
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

    for skill_name in skills_to_install:
        if skill_name not in all_skills:
            rprint(f"[red]Skill '{skill_name}' not found[/red]")
            rprint(f"[dim]Use 'asutils skill list --bundled' to see available skills[/dim]")
            continue

        # Epic skills and bundled commands go to commands directory, others to skills
        is_epic = skill_name.startswith("epic/")
        is_command = skill_name.startswith("commands/")
        if is_epic or is_command:
            target_dir = CLAUDE_COMMANDS_DIR
            # Strip 'epic/' or 'commands/' prefix for the installed name
            installed_name = skill_name.split("/", 1)[1]
        else:
            target_dir = CLAUDE_SKILLS_DIR
            installed_name = skill_name

        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{installed_name}.md"

        if target.exists() and not force:
            rprint(f"[yellow]'{installed_name}' already installed (use --force to overwrite)[/yellow]")
            continue

        source = all_skills[skill_name]
        target.write_text(source.read_text())
        location = "commands" if (is_epic or is_command) else "skills"
        rprint(f"[green]Added '{installed_name}' to ~/.claude/{location}/[/green]")


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
