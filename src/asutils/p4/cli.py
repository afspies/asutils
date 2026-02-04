"""CLI commands for Perforce exploration."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from asutils.p4 import api, config

app = typer.Typer(name="p4", help="Explore Epic's Perforce depot")


@app.command("setup")
def setup_cmd(
    skip_install: Annotated[bool, typer.Option("--skip-install", help="Skip p4 installation check")] = False,
    skip_claude: Annotated[bool, typer.Option("--skip-claude", help="Skip Claude Code agent/skill installation")] = False,
):
    """Interactive setup for Perforce CLI and configuration.

    Guides you through:
    1. Installing p4 CLI (via Homebrew on macOS)
    2. Configuring P4PORT (server address)
    3. Configuring P4USER (your username)
    4. Testing the connection
    5. Installing Claude Code agent and skill

    Examples:
        asutils p4 setup
        asutils p4 setup --skip-install
        asutils p4 setup --skip-claude
    """
    console = Console()

    console.print(Panel(
        "[bold]Perforce Setup for Epic Games[/bold]\n\n"
        "This will help you configure the Perforce CLI to connect to Epic's depot.",
        title="🔧 P4 Setup",
    ))

    # Step 1: Check if p4 is installed
    if not skip_install:
        rprint("\n[bold]Step 1: Checking p4 installation...[/bold]")
        p4_path = shutil.which("p4")

        if p4_path:
            rprint(f"[green]✓[/green] p4 found at: {p4_path}")
        else:
            rprint("[yellow]![/yellow] p4 command not found")

            # Check if brew is available (macOS)
            if shutil.which("brew"):
                rprint("\n[dim]Homebrew detected. You can install p4 with:[/dim]")
                rprint("  [cyan]brew install --cask p4[/cyan]")

                if typer.confirm("\nInstall p4 via Homebrew now?", default=True):
                    rprint("\n[dim]Running: brew install --cask p4[/dim]")
                    result = subprocess.run(
                        ["brew", "install", "--cask", "p4"],
                        capture_output=False,
                    )
                    if result.returncode == 0:
                        rprint("[green]✓[/green] p4 installed successfully")
                    else:
                        rprint("[red]✗[/red] Installation failed. Please install manually.")
                        raise typer.Exit(1)
                else:
                    rprint("\n[dim]Skipping installation. Install manually with:[/dim]")
                    rprint("  [cyan]brew install --cask p4[/cyan]")
                    rprint("\nThen run [cyan]asutils p4 setup --skip-install[/cyan] to continue.")
                    raise typer.Exit(0)
            else:
                rprint("\n[dim]Please install Perforce CLI manually:[/dim]")
                rprint("  macOS:   [cyan]brew install --cask p4[/cyan]")
                rprint("  Windows: Download from https://www.perforce.com/downloads/helix-command-line-client-p4")
                rprint("  Linux:   Use your package manager or download from Perforce")
                rprint("\nThen run [cyan]asutils p4 setup --skip-install[/cyan] to continue.")
                raise typer.Exit(1)

    # Step 2: Configure P4PORT
    rprint("\n[bold]Step 2: Configuring P4PORT (server address)...[/bold]")

    current_port = os.environ.get("P4PORT", "")
    if current_port:
        rprint(f"[dim]Current P4PORT:[/dim] {current_port}")

    rprint("\n[dim]Epic Perforce servers:[/dim]")
    rprint(f"  1. Internal network: [cyan]{config.SERVERS['internal']}[/cyan]")
    rprint(f"  2. VPN connection:   [cyan]{config.SERVERS['vpn']}[/cyan]")

    server_choice = typer.prompt(
        "\nWhich server? (1=internal, 2=vpn, or enter custom)",
        default="1" if not current_port else "skip",
    )

    if server_choice == "1":
        p4port = config.SERVERS["internal"]
    elif server_choice == "2":
        p4port = config.SERVERS["vpn"]
    elif server_choice.lower() == "skip":
        p4port = current_port
    else:
        p4port = server_choice

    if p4port and p4port != current_port:
        _add_to_shell_profile("P4PORT", p4port)

    # Step 3: Configure P4USER
    rprint("\n[bold]Step 3: Configuring P4USER (username)...[/bold]")

    current_user = os.environ.get("P4USER", "")
    if current_user:
        rprint(f"[dim]Current P4USER:[/dim] {current_user}")

    rprint("\n[dim]Your P4 username is typically: firstname.lastname[/dim]")
    rprint("[dim](Same as your Okta/Epic login, with a dot not underscore)[/dim]")

    default_user = current_user or ""
    p4user = typer.prompt(
        "\nEnter your P4 username",
        default=default_user if default_user else None,
    )

    if p4user and p4user != current_user:
        _add_to_shell_profile("P4USER", p4user)

    # Step 4: Test connection
    rprint("\n[bold]Step 4: Testing connection...[/bold]")

    # Temporarily set env vars for this process to test
    if p4port:
        os.environ["P4PORT"] = p4port
    if p4user:
        os.environ["P4USER"] = p4user

    success, message = config.verify_connection()

    if success:
        rprint(f"[green]✓[/green] {message}")
    else:
        rprint(f"[yellow]![/yellow] {message}")
        rprint("\n[dim]Connection not working yet. Common issues:[/dim]")
        rprint("  • Not connected to Epic network or VPN")
        rprint("  • Incorrect username format (should be firstname.lastname)")
        rprint("  • Need to authenticate: run [cyan]p4 login[/cyan]")
        rprint("\n[dim]After fixing, verify with:[/dim] [cyan]asutils p4 verify[/cyan]")

    # Step 5: Install Claude Code agent and skill
    if not skip_claude:
        rprint("\n[bold]Step 5: Installing Claude Code integration...[/bold]")

        try:
            from asutils.claude.agents import cli as agents_cli
            from asutils.claude import skill as skills_cli

            # Install the p4-explorer agent (function prints its own output)
            try:
                agents_cli.add_agent(name="epic/p4-explorer", all_agents=False, bundle=None, force=True)
            except Exception as e:
                rprint(f"[yellow]![/yellow] Could not install agent: {e}")

            # Install the p4 skill (function prints its own output)
            try:
                skills_cli.add_skill(name="epic/p4", bundle=None, force=True)
            except Exception as e:
                rprint(f"[yellow]![/yellow] Could not install skill: {e}")

        except ImportError as e:
            rprint(f"[yellow]![/yellow] Claude Code integration not available: {e}")

    # Final summary
    rprint("\n[bold green]Setup complete![/bold green]")
    rprint("\n[dim]Try these commands:[/dim]")
    rprint("  [cyan]asutils p4 ls fortnite[/cyan]     # List Fortnite depot")
    rprint("  [cyan]asutils p4 aliases[/cyan]        # Show all depot aliases")
    rprint("  [cyan]asutils p4 tree ue5 -d 2[/cyan]  # Browse UE5 structure")


def _add_to_shell_profile(var_name: str, value: str) -> None:
    """Add environment variable export to shell profile."""
    # Determine shell profile
    shell = os.environ.get("SHELL", "/bin/bash")
    if "zsh" in shell:
        profile = Path.home() / ".zshrc"
    else:
        profile = Path.home() / ".bashrc"

    export_line = f'export {var_name}="{value}"'

    # Check if already in profile
    if profile.exists():
        content = profile.read_text()
        if f"export {var_name}=" in content:
            rprint(f"[dim]Note: {var_name} already in {profile.name}, updating...[/dim]")
            # Replace existing line
            lines = content.split("\n")
            new_lines = []
            for line in lines:
                if line.strip().startswith(f"export {var_name}="):
                    new_lines.append(export_line)
                else:
                    new_lines.append(line)
            profile.write_text("\n".join(new_lines))
            rprint(f"[green]✓[/green] Updated {var_name} in {profile.name}")
            return

    # Append to profile
    with open(profile, "a") as f:
        f.write(f"\n# Perforce configuration (added by asutils p4 setup)\n")
        f.write(f"{export_line}\n")

    rprint(f"[green]✓[/green] Added {var_name} to {profile.name}")
    rprint(f"[dim]Run [cyan]source ~/{profile.name}[/cyan] or restart your terminal[/dim]")


@app.command("ls")
def ls_cmd(
    path: Annotated[str, typer.Argument(help="Depot path or alias")] = "//",
    files: Annotated[bool, typer.Option("-f", "--files", help="Include files")] = False,
    limit: Annotated[int, typer.Option("-l", "--limit", help="Max items")] = 50,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List directories (and optionally files) at depot path.

    Examples:
        asutils p4 ls fortnite              # Use alias
        asutils p4 ls //Fortnite/Main/      # Direct path
        asutils p4 ls ue5 -f                # Include files
    """
    try:
        resolved = config.resolve_depot_path(path)
        dirs = api.list_dirs(resolved)

        items = dirs
        if files:
            file_list = api.list_files(resolved, limit)
            items = dirs + file_list

        if json_output:
            rprint(json.dumps(items, indent=2))
        else:
            console = Console()
            table = Table(title=f"Contents of {resolved}")
            table.add_column("Type", style="dim", width=4)
            table.add_column("Path", style="cyan")

            for item in items[:limit]:
                icon = "📁" if item["type"] == "dir" else "📄"
                table.add_row(icon, item["path"])

            console.print(table)
            rprint(f"\n[dim]Found {len(dirs)} directories" + (f", {len(items) - len(dirs)} files" if files else "") + "[/dim]")

    except RuntimeError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("find")
def find_cmd(
    pattern: Annotated[str, typer.Argument(help="File pattern (supports wildcards)")],
    path: Annotated[str, typer.Option("-p", "--path", help="Search scope")] = "//...",
    limit: Annotated[int, typer.Option("-l", "--limit", help="Max results")] = 50,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Find files matching pattern.

    Examples:
        asutils p4 find "*.uasset" -p fortnite -l 100
        asutils p4 find "Build*.cs" -p ue5
        asutils p4 find "*PlayerController*"
    """
    try:
        files = api.search_files(pattern, path, limit)

        if json_output:
            rprint(json.dumps(files, indent=2))
        else:
            console = Console()
            scope = config.resolve_depot_path(path)
            table = Table(title=f"Files matching '{pattern}' in {scope}")
            table.add_column("Path", style="cyan")

            for f in files:
                table.add_row(f["path"])

            console.print(table)
            rprint(f"\n[dim]Found {len(files)} files" + (f" (limited to {limit})" if len(files) >= limit else "") + "[/dim]")

    except RuntimeError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("tree")
def tree_cmd(
    path: Annotated[str, typer.Argument(help="Depot path or alias")] = "//",
    depth: Annotated[int, typer.Option("-d", "--depth", help="Max depth")] = 2,
):
    """Show depot structure as tree.

    Examples:
        asutils p4 tree fortnite -d 2
        asutils p4 tree //Fortnite/Main/Source -d 3
    """
    try:
        resolved = config.resolve_depot_path(path)
        console = Console()

        tree = Tree(f"[bold cyan]{resolved}[/bold cyan]")
        _build_tree(tree, resolved, depth)

        console.print(tree)

    except RuntimeError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _build_tree(tree: Tree, path: str, depth: int) -> None:
    """Recursively build tree structure."""
    if depth <= 0:
        return

    try:
        dirs = api.list_dirs(path)
        for d in dirs[:20]:  # Limit breadth
            dir_name = d["path"].rsplit("/", 1)[-1]
            branch = tree.add(f"📁 {dir_name}")
            if depth > 1:
                _build_tree(branch, d["path"], depth - 1)
    except RuntimeError:
        tree.add("[dim]...[/dim]")


@app.command("info")
def info_cmd(
    path: Annotated[str, typer.Argument(help="File depot path")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Get detailed info about a file (fstat).

    Examples:
        asutils p4 info //Fortnite/Main/Build.cs
    """
    try:
        info = api.get_file_info(path)

        if json_output:
            rprint(json.dumps(info, indent=2))
        else:
            console = Console()
            table = Table(title=f"File Info: {path}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")

            for key, value in info.items():
                table.add_row(key, str(value))

            console.print(table)

    except RuntimeError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("history")
def history_cmd(
    path: Annotated[str, typer.Argument(help="File depot path")],
    limit: Annotated[int, typer.Option("-l", "--limit", help="Max entries")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Show file change history.

    Examples:
        asutils p4 history //Fortnite/Main/Build.cs -l 20
    """
    try:
        history = api.get_file_history(path, limit)

        if json_output:
            rprint(json.dumps(history, indent=2))
        else:
            console = Console()
            table = Table(title=f"History: {path}")
            table.add_column("#", style="cyan", width=4)
            table.add_column("CL", style="yellow", width=10)
            table.add_column("Action", style="green", width=8)
            table.add_column("Date", style="dim", width=12)
            table.add_column("User", style="magenta", width=20)
            table.add_column("Description", style="white", max_width=40)

            for h in history:
                desc = h.get("description", "")[:40]
                if len(h.get("description", "")) > 40:
                    desc += "..."
                table.add_row(
                    h.get("revision", ""),
                    h.get("change", ""),
                    h.get("action", ""),
                    h.get("date", ""),
                    h.get("user", ""),
                    desc,
                )

            console.print(table)

    except RuntimeError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("cat")
def cat_cmd(
    path: Annotated[str, typer.Argument(help="File depot path")],
    rev: Annotated[int | None, typer.Option("-r", "--rev", help="Specific revision")] = None,
):
    """Print file contents.

    Examples:
        asutils p4 cat //Fortnite/Main/Build.cs
        asutils p4 cat //Fortnite/Main/Build.cs -r 5
    """
    try:
        content = api.print_file(path, rev)
        rprint(content)

    except RuntimeError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("cl")
def changelist_cmd(
    changelist: Annotated[int, typer.Argument(help="Changelist number")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Show changelist details.

    Examples:
        asutils p4 cl 12345678
    """
    try:
        info = api.get_changelist(changelist)

        if json_output:
            rprint(json.dumps(info, indent=2))
        else:
            rprint(f"[bold]Changelist {changelist}[/bold]")
            rprint(f"[dim]User:[/dim] {info['user']}")
            rprint(f"[dim]Date:[/dim] {info['date']}")
            rprint(f"\n[dim]Description:[/dim]")
            rprint(info["description"])

            if info["files"]:
                rprint(f"\n[bold]Files ({len(info['files'])}):[/bold]")
                for f in info["files"][:20]:
                    rprint(f"  {f}")
                if len(info["files"]) > 20:
                    rprint(f"  [dim]... and {len(info['files']) - 20} more[/dim]")

    except RuntimeError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("where")
def where_cmd(
    path: Annotated[str, typer.Argument(help="Depot path")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Show local workspace mapping for depot path.

    Examples:
        asutils p4 where //Fortnite/Main/Source/
    """
    try:
        mapping = api.where(path)

        if json_output:
            rprint(json.dumps(mapping, indent=2))
        else:
            if "error" in mapping:
                rprint(f"[yellow]{mapping['error']}[/yellow]")
            else:
                rprint(f"[dim]Depot:[/dim]  {mapping['depot']}")
                rprint(f"[dim]Client:[/dim] {mapping['client']}")
                rprint(f"[dim]Local:[/dim]  {mapping['local']}")

    except RuntimeError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("aliases")
def aliases_cmd():
    """Show available depot path aliases.

    Examples:
        asutils p4 aliases
    """
    console = Console()
    table = Table(title="Depot Aliases")
    table.add_column("Alias", style="cyan")
    table.add_column("Path", style="white")

    # Group by resolved path to show primary aliases
    seen = {}
    for alias, path in sorted(config.DEPOT_ALIASES.items()):
        if path not in seen:
            seen[path] = []
        seen[path].append(alias)

    for path, aliases in sorted(seen.items(), key=lambda x: x[0]):
        alias_str = ", ".join(sorted(aliases, key=len))
        table.add_row(alias_str, path)

    console.print(table)


@app.command("branches")
def branches_cmd(
    depot: Annotated[str, typer.Argument(help="Depot name or alias (fortnite, ue5, etc.)")] = "fortnite",
    filter_pattern: Annotated[str | None, typer.Option("-f", "--filter", help="Filter pattern (Dev-*, Release-*, *Valkyrie*)")] = None,
    dev_only: Annotated[bool, typer.Option("--dev", help="Show only Dev branches")] = False,
    release_only: Annotated[bool, typer.Option("--release", help="Show only Release branches")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List available branches for a depot.

    Examples:
        asutils p4 branches fortnite              # All Fortnite branches
        asutils p4 branches fn --dev              # Only Dev branches
        asutils p4 branches ue5 --release         # Only Release branches
        asutils p4 branches fn -f "*Valkyrie*"    # Filter by pattern
    """
    try:
        # Apply type filter
        if dev_only:
            filter_pattern = "Dev-*"
        elif release_only:
            filter_pattern = "Release-*"

        branches = api.list_branches(depot, filter_pattern)

        if json_output:
            rprint(json.dumps(branches, indent=2))
        else:
            console = Console()
            table = Table(title=f"Branches in {depot}")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="yellow", width=8)
            table.add_column("Path", style="dim")

            # Sort: Main first, then Dev, then Release
            type_order = {"main": 0, "dev": 1, "release": 2, "other": 3}
            sorted_branches = sorted(branches, key=lambda b: (type_order.get(b["type"], 3), b["name"]))

            for b in sorted_branches:
                type_style = {
                    "main": "[bold green]main[/bold green]",
                    "dev": "[cyan]dev[/cyan]",
                    "release": "[yellow]release[/yellow]",
                    "other": "[dim]other[/dim]",
                }.get(b["type"], b["type"])
                table.add_row(b["name"], type_style, b["path"])

            console.print(table)
            rprint(f"\n[dim]Found {len(branches)} branches[/dim]")
            rprint("[dim]Use path directly: asutils p4 ls //Fortnite/Dev-Valkyrie/[/dim]")

    except RuntimeError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("verify")
def verify_cmd():
    """Verify P4 connection is working.

    Examples:
        asutils p4 verify
    """
    success, message = config.verify_connection()

    if success:
        rprint(f"[green]✓[/green] {message}")
    else:
        rprint(f"[red]✗[/red] {message}")
        rprint(f"\n{config.get_server_suggestion()}")
        raise typer.Exit(1)


@app.command("status")
def status_cmd():
    """Show current P4 configuration.

    Examples:
        asutils p4 status
    """
    console = Console()

    # Get config
    p4_config = config.get_p4_config()

    table = Table(title="P4 Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    for key in ["P4PORT", "P4USER", "P4CLIENT", "P4CONFIG"]:
        value = p4_config.get(key, "[dim]not set[/dim]")
        table.add_row(key, value)

    console.print(table)

    # Try connection
    rprint("\n[bold]Connection Status:[/bold]")
    success, message = config.verify_connection()
    if success:
        rprint(f"[green]✓[/green] {message}")
    else:
        rprint(f"[yellow]![/yellow] {message}")
        rprint(f"\n{config.get_server_suggestion()}")


if __name__ == "__main__":
    app()
