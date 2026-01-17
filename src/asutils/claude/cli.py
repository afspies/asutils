"""Claude Code utilities CLI."""

import subprocess
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console

from asutils.claude import skill
from asutils.claude.agents import cli as agents
from asutils.claude.permissions import cli as permission
from asutils.claude.tts import cli as tts
from asutils.envsetup import cli as env

app = typer.Typer(name="claude", help="Claude Code utilities")
app.add_typer(skill.app, name="skill")
app.add_typer(permission.app, name="permission")
app.add_typer(agents.app, name="agent")
app.add_typer(tts.app, name="tts")


@app.command("setup")
def setup(
    profile: Annotated[
        str, typer.Option("--profile", "-p", help="Permission profile to set as default")
    ] = "dev",
    skill_bundle: Annotated[
        str, typer.Option("--skills", "-s", help="Skill bundle to install")
    ] = "default",
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing files")
    ] = False,
):
    """One-command setup for Claude Code with permissions, skills, and agents.

    Installs permission profiles, sets a default profile, installs skills, and adds agents.
    """
    console = Console()

    console.print("[bold]Setting up Claude Code...[/bold]\n")

    # Step 1: Install permission profiles and hook
    console.print("[bold cyan]Step 1:[/bold cyan] Installing permission profiles...")
    permission.install_profiles(force=force)
    console.print()

    # Step 2: Set default permission profile
    console.print(f"[bold cyan]Step 2:[/bold cyan] Setting default profile to '{profile}'...")
    permission.manage_default(name=profile)
    console.print()

    # Step 3: Install skills
    console.print(f"[bold cyan]Step 3:[/bold cyan] Installing '{skill_bundle}' skill bundle...")
    skill.add_skill(name=None, bundle=skill_bundle, force=force)
    console.print()

    # Step 4: Install agents
    console.print("[bold cyan]Step 4:[/bold cyan] Installing agents...")
    agents.add_agent(name=None, all_agents=True, force=force)
    console.print()

    # Step 5: Install Anthropic plugins
    console.print("[bold cyan]Step 5:[/bold cyan] Installing Anthropic plugins...")
    try:
        result = subprocess.run(
            ["claude", "plugin", "install", "code-simplifier"],
            capture_output=True,
            text=True,
            check=True,
        )
        console.print("  [green]✓[/green] code-simplifier plugin installed")
    except subprocess.CalledProcessError as e:
        console.print(f"  [yellow]⚠[/yellow] Failed to install code-simplifier: {e.stderr.strip()}")
    except FileNotFoundError:
        console.print("  [yellow]⚠[/yellow] 'claude' CLI not found - skipping plugin installation")
    console.print()

    # Step 6: Configure environment (aliases, tmux)
    console.print("[bold cyan]Step 6:[/bold cyan] Configuring environment (aliases, tmux)...")
    env.setup_env(force=force)
    console.print()

    console.print("[bold green]Setup complete![/bold green]")
    rprint("\n[dim]Claude Code is now configured with:[/dim]")
    rprint("  - Permission profiles installed")
    rprint(f"  - Default profile: [cyan]{profile}[/cyan]")
    rprint(f"  - Skills: [cyan]{skill_bundle}[/cyan] bundle")
    rprint("  - All bundled agents installed")
    rprint("  - Anthropic plugins: [cyan]code-simplifier[/cyan]")
    rprint("  - Shell aliases (cc, ccc, cg, cgc)")
    rprint("  - Tmux configuration (if installed)")
    rprint("\n[dim]Run 'claude' to start using it![/dim]")


if __name__ == "__main__":
    app()
