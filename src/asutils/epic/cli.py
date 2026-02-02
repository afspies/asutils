"""CLI commands for Epic Games specific setup and utilities."""

from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console

app = typer.Typer(name="epic", help="Epic Games specific utilities")


@app.command("setup")
def setup(
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite existing config")] = False,
    skip_skills: Annotated[bool, typer.Option("--skip-skills", help="Skip skill installation")] = False,
    skip_verify: Annotated[bool, typer.Option("--skip-verify", help="Skip auth verification")] = False,
):
    """Set up Epic Games integrations (Confluence, JIRA, skills).

    This command:
    1. Creates/updates Epic config file
    2. Verifies JIRA_API_TOKEN authentication
    3. Installs Epic Claude Code skills

    Examples:
        asutils epic setup
        asutils epic setup --force
    """
    console = Console()

    console.print("[bold]Setting up Epic Games integrations...[/bold]\n")

    # Step 1: Create config
    console.print("[bold cyan]Step 1:[/bold cyan] Checking configuration...")
    _setup_config(force)
    console.print()

    # Step 2: Verify auth
    if not skip_verify:
        console.print("[bold cyan]Step 2:[/bold cyan] Verifying authentication...")
        _verify_auth()
        console.print()

    # Step 3: Install skills
    if not skip_skills:
        console.print("[bold cyan]Step 3:[/bold cyan] Installing Epic skills...")
        _install_skills(force)
        console.print()

    console.print("[bold green]Epic setup complete![/bold green]\n")
    rprint("[dim]You can now use:[/dim]")
    rprint("  - asutils confluence search \"query\"")
    rprint("  - /jira (Claude Code command)")
    rprint("  - /confluence (Claude Code command)")


@app.command("status")
def status():
    """Show status of Epic integrations."""
    console = Console()
    console.print("[bold]Epic Integration Status[/bold]\n")

    # Check config
    from asutils.confluence.config import CONFIG_FILE, get_config

    if CONFIG_FILE.exists():
        rprint(f"[green]✓[/green] Config file: {CONFIG_FILE}")
        config = get_config()
        rprint(f"  Confluence: {config.get('confluence', {}).get('base_url', 'not set')}")
        rprint(f"  Email: {config.get('confluence', {}).get('email', 'not set')}")
    else:
        rprint(f"[yellow]○[/yellow] Config file not found: {CONFIG_FILE}")

    # Check token
    import os

    if os.environ.get("JIRA_API_TOKEN"):
        rprint("[green]✓[/green] JIRA_API_TOKEN is set")
    else:
        rprint("[red]✗[/red] JIRA_API_TOKEN not set")

    # Check auth
    console.print()
    try:
        from asutils.confluence import verify_auth

        verify_auth()
        rprint("[green]✓[/green] Confluence authentication working")
    except Exception as e:
        rprint(f"[red]✗[/red] Confluence authentication failed: {e}")

    # Check skills
    console.print()
    from pathlib import Path

    commands_dir = Path.home() / ".claude" / "commands"
    for skill in ["jira", "confluence"]:
        skill_path = commands_dir / f"{skill}.md"
        if skill_path.exists():
            rprint(f"[green]✓[/green] /{skill} skill installed")
        else:
            rprint(f"[yellow]○[/yellow] /{skill} skill not installed")


@app.command("verify")
def verify():
    """Verify Epic authentication is working."""
    console = Console()

    try:
        from asutils.confluence import verify_auth

        console.print("Verifying Confluence authentication...")
        verify_auth()
        rprint("[green]✓[/green] Authentication successful!")

        # Show some info
        from asutils.confluence import list_spaces

        spaces = list_spaces(limit=5)
        rprint(f"\n[dim]Found {len(spaces)} spaces (showing first 5):[/dim]")
        for s in spaces[:5]:
            rprint(f"  - {s['key']}: {s['name']}")

    except Exception as e:
        rprint(f"[red]✗[/red] Authentication failed: {e}")
        raise typer.Exit(1)


def _setup_config(force: bool) -> None:
    """Create or update Epic config file."""
    from asutils.confluence.config import CONFIG_FILE, DEFAULT_CONFIG, get_config, save_config

    if CONFIG_FILE.exists() and not force:
        rprint(f"  [green]✓[/green] Config exists: {CONFIG_FILE}")
        return

    config = get_config()
    save_config(config)
    action = "Updated" if CONFIG_FILE.exists() else "Created"
    rprint(f"  [green]✓[/green] {action} config: {CONFIG_FILE}")


def _verify_auth() -> None:
    """Verify authentication with Confluence."""
    import os

    if not os.environ.get("JIRA_API_TOKEN"):
        rprint("  [red]✗[/red] JIRA_API_TOKEN not set")
        rprint("  [dim]Set it with: export JIRA_API_TOKEN='your-token'[/dim]")
        raise typer.Exit(1)

    try:
        from asutils.confluence import verify_auth

        verify_auth()
        rprint("  [green]✓[/green] Authentication verified")
    except Exception as e:
        rprint(f"  [red]✗[/red] Authentication failed: {e}")
        raise typer.Exit(1)


def _install_skills(force: bool) -> None:
    """Install Epic skills to Claude Code."""
    try:
        from asutils.claude.skill import add_skill

        add_skill(name=None, bundle="epic", force=force)
    except Exception as e:
        rprint(f"  [yellow]⚠[/yellow] Failed to install skills: {e}")
        rprint("  [dim]You can install manually: asutils claude skill add --bundle epic[/dim]")


if __name__ == "__main__":
    app()
