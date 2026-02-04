"""Agent management CLI for Claude Code."""

from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

app = typer.Typer(help="Manage Claude Code custom agents")

# Bundled agents directory (alongside this module)
BUNDLED_AGENTS_DIR = Path(__file__).parent / "definitions"

# Epic Games specific agents (markdown format with YAML frontmatter)
EPIC_AGENTS_DIR = Path(__file__).parent / "epic"

# Claude Code agents directory
CLAUDE_AGENTS_DIR = Path.home() / ".claude" / "agents"


def get_bundled_agents() -> dict[str, Path]:
    """Return dict of agent_name -> path for all bundled agents (YAML format)."""
    agents = {}
    if BUNDLED_AGENTS_DIR.exists():
        for f in BUNDLED_AGENTS_DIR.glob("*.yaml"):
            agents[f.stem] = f
    return agents


def get_epic_agents() -> dict[str, Path]:
    """Return dict of agent_name -> path for Epic Games specific agents (markdown format)."""
    agents = {}
    if EPIC_AGENTS_DIR.exists():
        for f in EPIC_AGENTS_DIR.glob("*.md"):
            agents[f.stem] = f
    return agents


def get_all_available_agents() -> dict[str, Path]:
    """Return dict of all agents including epic (prefixed with 'epic/')."""
    agents = get_bundled_agents()
    for name, path in get_epic_agents().items():
        agents[f"epic/{name}"] = path
    return agents


def load_agent_config_from_markdown(path: Path) -> dict:
    """Load agent configuration from markdown file with YAML frontmatter."""
    content = path.read_text()
    if content.startswith("---"):
        _, frontmatter, _ = content.split("---", 2)
        return yaml.safe_load(frontmatter)
    return {}


def get_installed_agents() -> dict[str, Path]:
    """Return dict of agent_name -> path for installed agents (YAML and markdown)."""
    agents = {}
    if CLAUDE_AGENTS_DIR.exists():
        for f in CLAUDE_AGENTS_DIR.glob("*.yaml"):
            agents[f.stem] = f
        for f in CLAUDE_AGENTS_DIR.glob("*.md"):
            agents[f.stem] = f
    return agents


def load_agent_config(path: Path) -> dict:
    """Load agent configuration from YAML or markdown file."""
    if path.suffix == ".md":
        return load_agent_config_from_markdown(path)
    with open(path) as f:
        return yaml.safe_load(f)


@app.command("list")
def list_agents(
    bundled: Annotated[bool, typer.Option("--bundled", "-b", help="Show bundled agents")] = False,
    installed: Annotated[
        bool, typer.Option("--installed", "-i", help="Show installed agents")
    ] = False,
    epic: Annotated[bool, typer.Option("--epic", "-e", help="Show Epic Games agents")] = False,
):
    """List available and installed agents."""
    # Default to showing all if none specified
    if not bundled and not installed and not epic:
        bundled = installed = epic = True

    console = Console()
    bundled_agents = get_bundled_agents()
    epic_agents = get_epic_agents()
    installed_agents = get_installed_agents()

    if bundled:
        table = Table(title="Bundled Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        table.add_column("Installed", style="green")

        for name, path in sorted(bundled_agents.items()):
            config = load_agent_config(path)
            desc = config.get("description", "")[:50]
            is_installed = name in installed_agents
            table.add_row(name, desc, "yes" if is_installed else "no")

        if not bundled_agents:
            console.print("[dim]No bundled agents available[/dim]")
        else:
            console.print(table)

    if epic:
        if bundled:
            console.print()

        table = Table(title="Epic Games Agents (use --bundle epic to install)")
        table.add_column("Name", style="magenta")
        table.add_column("Description")
        table.add_column("Installed", style="green")

        for name, path in sorted(epic_agents.items()):
            config = load_agent_config(path)
            desc = config.get("description", "")
            # Truncate multi-line descriptions
            if "\n" in desc:
                desc = desc.split("\n")[0]
            desc = desc[:50]
            is_installed = name in installed_agents
            table.add_row(f"epic/{name}", desc, "yes" if is_installed else "no")

        if not epic_agents:
            console.print("[dim]No Epic Games agents available[/dim]")
        else:
            console.print(table)

    if installed:
        if bundled or epic:
            console.print()  # Spacing between tables

        table = Table(title="Installed Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        table.add_column("Source", style="yellow")

        for name, path in sorted(installed_agents.items()):
            config = load_agent_config(path)
            desc = config.get("description", "")
            if "\n" in desc:
                desc = desc.split("\n")[0]
            desc = desc[:50]
            if name in bundled_agents:
                source = "bundled"
            elif name in epic_agents:
                source = "epic"
            else:
                source = "custom"
            table.add_row(name, desc, source)

        if not installed_agents:
            console.print("[dim]No agents installed[/dim]")
        else:
            console.print(table)


@app.command("show")
def show_agent(
    name: Annotated[str, typer.Argument(help="Agent name to show (use 'epic/name' for Epic agents)")],
    installed: Annotated[
        bool, typer.Option("--installed", "-i", help="Show installed version")
    ] = False,
):
    """Show the configuration of an agent."""
    console = Console()

    if installed:
        agents = get_installed_agents()
        source = "installed"
    else:
        agents = get_all_available_agents()
        source = "bundled"

    # Handle epic/ prefix
    lookup_name = name
    if name.startswith("epic/"):
        lookup_name = name
    elif name not in agents and f"epic/{name}" in agents:
        lookup_name = f"epic/{name}"

    if lookup_name not in agents:
        rprint(f"[red]Agent '{name}' not found in {source} agents[/red]")
        raise typer.Exit(1)

    path = agents[lookup_name]
    content = path.read_text()
    config = load_agent_config(path)

    # Show summary panel
    desc = config.get('description', 'No description')
    console.print(Panel(
        f"[bold]{config.get('name', name)}[/bold]\n\n{desc}",
        title=f"Agent: {lookup_name}",
        subtitle=f"{source}: {path}",
    ))
    console.print()

    # Show full config (YAML or markdown)
    syntax_lang = "markdown" if path.suffix == ".md" else "yaml"
    syntax = Syntax(content, syntax_lang, theme="monokai", line_numbers=True)
    console.print(syntax)

    if installed:
        console.print(f"\n[dim]Edit at: {path}[/dim]")


@app.command("add")
def add_agent(
    name: Annotated[str | None, typer.Argument(help="Agent name to add (use 'epic/name' for Epic agents)")] = None,
    all_agents: Annotated[bool, typer.Option("--all", "-a", help="Add all bundled agents")] = False,
    bundle: Annotated[str | None, typer.Option("--bundle", "-b", help="Add agents from bundle (e.g., 'epic')")] = None,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing agents")
    ] = False,
):
    """Add an agent to Claude Code's agents directory.

    For Epic Games specific agents, use 'epic/agentname' or --bundle epic.
    """
    if name is None and not all_agents and bundle is None:
        rprint("[red]Provide an agent name, --all, or --bundle[/red]")
        raise typer.Exit(1)

    all_available = get_all_available_agents()
    bundled = get_bundled_agents()
    epic = get_epic_agents()
    installed = get_installed_agents()

    # Determine which agents to install
    if bundle == "epic":
        agents_to_install = [f"epic/{name}" for name in epic.keys()]
    elif all_agents:
        agents_to_install = list(bundled.keys())
    else:
        # Handle epic/ prefix or auto-detect
        if name.startswith("epic/"):
            agents_to_install = [name]
        elif name not in all_available and f"epic/{name}" in all_available:
            agents_to_install = [f"epic/{name}"]
        else:
            agents_to_install = [name]

    if not agents_to_install:
        rprint("[yellow]No agents to install[/yellow]")
        return

    # Ensure target directory exists
    CLAUDE_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    for agent_name in agents_to_install:
        if agent_name not in all_available:
            rprint(f"[red]Agent '{agent_name}' not found in available agents[/red]")
            continue

        source = all_available[agent_name]

        # Use the base name for the installed file (strip epic/ prefix)
        if agent_name.startswith("epic/"):
            installed_name = agent_name.split("/", 1)[1]
        else:
            installed_name = agent_name

        # Preserve file extension
        ext = source.suffix
        target = CLAUDE_AGENTS_DIR / f"{installed_name}{ext}"

        if installed_name in installed and not force:
            rprint(f"[yellow]'{installed_name}' already installed (use --force to overwrite)[/yellow]")
            continue

        target.write_text(source.read_text())
        rprint(f"[green]Added '{installed_name}' to {target}[/green]")


@app.command("remove")
def remove_agent(
    name: Annotated[str | None, typer.Argument(help="Agent name to remove")] = None,
    all_agents: Annotated[bool, typer.Option("--all", help="Remove all agents")] = False,
):
    """Remove an agent from Claude Code's agents directory."""
    if name is None and not all_agents:
        rprint("[red]Provide an agent name or use --all[/red]")
        raise typer.Exit(1)

    installed = get_installed_agents()

    if all_agents:
        agents_to_remove = list(installed.keys())
    else:
        agents_to_remove = [name] if name in installed else []

    if not agents_to_remove:
        rprint("[yellow]No matching agents to remove[/yellow]")
        return

    for agent_name in agents_to_remove:
        path = installed[agent_name]
        path.unlink()
        rprint(f"[green]Removed '{agent_name}' from {path}[/green]")


if __name__ == "__main__":
    app()
