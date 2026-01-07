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

# Claude Code agents directory
CLAUDE_AGENTS_DIR = Path.home() / ".claude" / "agents"


def get_bundled_agents() -> dict[str, Path]:
    """Return dict of agent_name -> path for all bundled agents."""
    agents = {}
    if BUNDLED_AGENTS_DIR.exists():
        for f in BUNDLED_AGENTS_DIR.glob("*.yaml"):
            agents[f.stem] = f
    return agents


def get_installed_agents() -> dict[str, Path]:
    """Return dict of agent_name -> path for installed agents."""
    agents = {}
    if CLAUDE_AGENTS_DIR.exists():
        for f in CLAUDE_AGENTS_DIR.glob("*.yaml"):
            agents[f.stem] = f
    return agents


def load_agent_config(path: Path) -> dict:
    """Load agent configuration from YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


@app.command("list")
def list_agents(
    bundled: Annotated[bool, typer.Option("--bundled", "-b", help="Show bundled agents")] = False,
    installed: Annotated[
        bool, typer.Option("--installed", "-i", help="Show installed agents")
    ] = False,
):
    """List available and installed agents."""
    # Default to showing both if neither specified
    if not bundled and not installed:
        bundled = installed = True

    console = Console()
    bundled_agents = get_bundled_agents()
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

    if installed:
        if bundled:
            console.print()  # Spacing between tables

        table = Table(title="Installed Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        table.add_column("Source", style="yellow")

        for name, path in sorted(installed_agents.items()):
            config = load_agent_config(path)
            desc = config.get("description", "")[:50]
            source = "bundled" if name in bundled_agents else "custom"
            table.add_row(name, desc, source)

        if not installed_agents:
            console.print("[dim]No agents installed[/dim]")
        else:
            console.print(table)


@app.command("show")
def show_agent(
    name: Annotated[str, typer.Argument(help="Agent name to show")],
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
        agents = get_bundled_agents()
        source = "bundled"

    if name not in agents:
        rprint(f"[red]Agent '{name}' not found in {source} agents[/red]")
        raise typer.Exit(1)

    path = agents[name]
    content = path.read_text()
    config = yaml.safe_load(content)

    # Show summary panel
    console.print(Panel(
        f"[bold]{config.get('name', name)}[/bold]\n\n{config.get('description', 'No description')}",
        title=f"Agent: {name}",
        subtitle=f"{source}: {path}",
    ))
    console.print()

    # Show full YAML config
    syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
    console.print(syntax)

    if installed:
        console.print(f"\n[dim]Edit at: {path}[/dim]")


@app.command("add")
def add_agent(
    name: Annotated[str | None, typer.Argument(help="Agent name to add")] = None,
    all_agents: Annotated[bool, typer.Option("--all", "-a", help="Add all bundled agents")] = False,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing agents")
    ] = False,
):
    """Add an agent to Claude Code's agents directory."""
    if name is None and not all_agents:
        rprint("[red]Provide an agent name or use --all[/red]")
        raise typer.Exit(1)

    bundled = get_bundled_agents()
    installed = get_installed_agents()

    # Determine which agents to install
    if all_agents:
        agents_to_install = list(bundled.keys())
    else:
        agents_to_install = [name]

    if not agents_to_install:
        rprint("[yellow]No agents to install[/yellow]")
        return

    # Ensure target directory exists
    CLAUDE_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    for agent_name in agents_to_install:
        if agent_name not in bundled:
            rprint(f"[red]Agent '{agent_name}' not found in bundled agents[/red]")
            continue

        target = CLAUDE_AGENTS_DIR / f"{agent_name}.yaml"

        if agent_name in installed and not force:
            rprint(f"[yellow]'{agent_name}' already installed (use --force to overwrite)[/yellow]")
            continue

        source = bundled[agent_name]
        target.write_text(source.read_text())
        rprint(f"[green]Added '{agent_name}' to {target}[/green]")


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
