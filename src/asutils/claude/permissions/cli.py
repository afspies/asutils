"""Permission profile CLI for Claude Code."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

app = typer.Typer(help="Manage Claude Code permission profiles")

# Bundled profiles directory (alongside this module)
BUNDLED_PROFILES_DIR = Path(__file__).parent / "profiles"
BUNDLED_HOOK = Path(__file__).parent / "hook.py"

# Claude Code directories
CLAUDE_DIR = Path.home() / ".claude"
CLAUDE_PROFILES_DIR = CLAUDE_DIR / "profiles"
CLAUDE_HOOKS_DIR = CLAUDE_DIR / "hooks"
CLAUDE_SETTINGS = CLAUDE_DIR / "settings.json"
DEFAULT_PROFILE_FILE = CLAUDE_DIR / "default-profile"

HOOK_FILENAME = "permission-router.py"


def get_bundled_profiles() -> dict[str, Path]:
    """Return dict of profile_name -> path for all bundled profiles."""
    profiles = {}
    if BUNDLED_PROFILES_DIR.exists():
        for f in BUNDLED_PROFILES_DIR.glob("*.yaml"):
            profiles[f.stem] = f
    return profiles


def get_installed_profiles() -> dict[str, Path]:
    """Return dict of profile_name -> path for installed profiles."""
    profiles = {}
    if CLAUDE_PROFILES_DIR.exists():
        for f in CLAUDE_PROFILES_DIR.glob("*.yaml"):
            profiles[f.stem] = f
    return profiles


def is_hook_installed() -> bool:
    """Check if the permission hook is installed in settings.json."""
    if not CLAUDE_SETTINGS.exists():
        return False
    try:
        settings = json.loads(CLAUDE_SETTINGS.read_text())
        hooks = settings.get("hooks", {})
        permission_hooks = hooks.get("PermissionRequest", [])
        for hook_entry in permission_hooks:
            # New format: {"matcher": {...}, "hooks": [...]}
            if "hooks" in hook_entry:
                for h in hook_entry.get("hooks", []):
                    if HOOK_FILENAME in h.get("command", ""):
                        return True
            # Old format: {"type": "command", "command": "..."}
            elif HOOK_FILENAME in hook_entry.get("command", ""):
                return True
    except (json.JSONDecodeError, KeyError):
        pass
    return False


def get_current_profile() -> str:
    """Get the current default profile name."""
    import os

    # Environment variable takes precedence
    env_profile = os.environ.get("CLAUDE_PROFILE")
    if env_profile:
        return env_profile

    # Check default profile file
    if DEFAULT_PROFILE_FILE.exists():
        content = DEFAULT_PROFILE_FILE.read_text().strip()
        if content:
            return content

    return "default"


@app.command("list")
def list_profiles(
    bundled: Annotated[
        bool, typer.Option("--bundled", "-b", help="Show bundled profiles")
    ] = False,
    installed: Annotated[
        bool, typer.Option("--installed", "-i", help="Show installed profiles")
    ] = False,
):
    """List available permission profiles."""
    # Default to showing both if neither specified
    if not bundled and not installed:
        bundled = installed = True

    console = Console()
    bundled_profiles = get_bundled_profiles()
    installed_profiles = get_installed_profiles()

    if bundled:
        table = Table(title="Bundled Profiles")
        table.add_column("Name", style="cyan")
        table.add_column("Installed", style="green")
        table.add_column("Path")

        for name, path in sorted(bundled_profiles.items()):
            is_installed = name in installed_profiles
            table.add_row(name, "yes" if is_installed else "no", str(path))

        console.print(table)

    if installed:
        if bundled:
            console.print()  # Spacing between tables

        table = Table(title="Installed Profiles")
        table.add_column("Name", style="cyan")
        table.add_column("Source", style="yellow")
        table.add_column("Path")

        for name, path in sorted(installed_profiles.items()):
            source = "bundled" if name in bundled_profiles else "custom"
            table.add_row(name, source, str(path))

        if not installed_profiles:
            console.print("[dim]No profiles installed[/dim]")
        else:
            console.print(table)


@app.command("show")
def show_profile(
    name: Annotated[str, typer.Argument(help="Profile name to show")],
    installed: Annotated[
        bool, typer.Option("--installed", "-i", help="Show installed version")
    ] = False,
):
    """Show the content of a permission profile."""
    console = Console()

    if installed:
        profiles = get_installed_profiles()
        source = "installed"
    else:
        profiles = get_bundled_profiles()
        source = "bundled"

    if name not in profiles:
        rprint(f"[red]Profile '{name}' not found in {source} profiles[/red]")
        raise typer.Exit(1)

    path = profiles[name]
    content = path.read_text()

    console.print(f"[dim]# {source}: {path}[/dim]\n")
    syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
    console.print(syntax)

    if installed:
        console.print(f"\n[dim]Edit at: {path}[/dim]")


@app.command("install")
def install_profiles(
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing files")
    ] = False,
):
    """Install permission profiles and hook to ~/.claude/."""
    console = Console()

    # Create directories
    CLAUDE_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    CLAUDE_HOOKS_DIR.mkdir(parents=True, exist_ok=True)

    # Copy profiles
    bundled = get_bundled_profiles()
    installed = get_installed_profiles()

    console.print("[bold]Installing profiles...[/bold]")
    for name, source_path in bundled.items():
        target = CLAUDE_PROFILES_DIR / f"{name}.yaml"
        if name in installed and not force:
            console.print(f"  [yellow]'{name}' exists (use --force to overwrite)[/yellow]")
        else:
            target.write_text(source_path.read_text())
            console.print(f"  [green]Installed '{name}'[/green]")

    # Copy hook script
    console.print("\n[bold]Installing hook script...[/bold]")
    hook_target = CLAUDE_HOOKS_DIR / HOOK_FILENAME
    if hook_target.exists() and not force:
        console.print("  [yellow]Hook exists (use --force to overwrite)[/yellow]")
    else:
        hook_target.write_text(BUNDLED_HOOK.read_text())
        hook_target.chmod(0o755)
        console.print(f"  [green]Installed {hook_target}[/green]")

    # Update settings.json
    console.print("\n[bold]Configuring settings.json...[/bold]")
    hook_command = f"python3 {hook_target}"

    if CLAUDE_SETTINGS.exists():
        try:
            settings = json.loads(CLAUDE_SETTINGS.read_text())
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}

    # Ensure hooks structure exists
    if "hooks" not in settings:
        settings["hooks"] = {}
    if "PermissionRequest" not in settings["hooks"]:
        settings["hooks"]["PermissionRequest"] = []

    # Check if hook already configured (new format with matcher/hooks)
    def has_our_hook(hook_entry):
        # New format: {"matcher": {...}, "hooks": [...]}
        if "hooks" in hook_entry:
            return any(
                HOOK_FILENAME in h.get("command", "")
                for h in hook_entry.get("hooks", [])
            )
        # Old format: {"type": "command", "command": "..."}
        return HOOK_FILENAME in hook_entry.get("command", "")

    hook_exists = any(has_our_hook(h) for h in settings["hooks"]["PermissionRequest"])

    if hook_exists and not force:
        console.print("  [yellow]Hook already configured in settings.json[/yellow]")
    else:
        # Remove old hook if forcing
        if force:
            settings["hooks"]["PermissionRequest"] = [
                h
                for h in settings["hooks"]["PermissionRequest"]
                if not has_our_hook(h)
            ]
        # Add new hook using new format with matcher
        settings["hooks"]["PermissionRequest"].append({
            "matcher": "*",  # Match all tools
            "hooks": [{"type": "command", "command": hook_command}]
        })
        CLAUDE_SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
        console.print("  [green]Added hook to settings.json[/green]")

    console.print("\n[bold green]Installation complete![/bold green]")
    console.print("\n[dim]Usage:[/dim]")
    console.print("  claude                          # Uses default profile")
    console.print("  CLAUDE_PROFILE=dev claude       # Uses dev profile")
    console.print("  asutils claude permission default dev  # Set default to dev")


@app.command("status")
def show_status():
    """Show permission profile installation status."""
    console = Console()

    installed_profiles = get_installed_profiles()
    hook_installed = is_hook_installed()
    hook_file_exists = (CLAUDE_HOOKS_DIR / HOOK_FILENAME).exists()
    current_profile = get_current_profile()

    # Overall status
    if hook_installed and hook_file_exists and installed_profiles:
        console.print(Panel("[bold green]Permission profiles installed and active[/bold green]"))
    else:
        console.print(Panel("[bold yellow]Permission profiles not fully installed[/bold yellow]"))

    console.print()

    # Details table
    table = Table(title="Status Details")
    table.add_column("Component", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    # Profiles
    if installed_profiles:
        table.add_row(
            "Profiles",
            "[green]Installed[/green]",
            f"{len(installed_profiles)} profiles in {CLAUDE_PROFILES_DIR}",
        )
    else:
        table.add_row("Profiles", "[red]Missing[/red]", "Run: asutils claude permission install")

    # Hook file
    hook_path = str(CLAUDE_HOOKS_DIR / HOOK_FILENAME)
    if hook_file_exists:
        table.add_row("Hook script", "[green]Installed[/green]", hook_path)
    else:
        table.add_row("Hook script", "[red]Missing[/red]", "Run: asutils claude permission install")

    # Settings config
    install_cmd = "asutils claude permission install"
    if hook_installed:
        table.add_row("Settings.json", "[green]Configured[/green]", "Hook in PermissionRequest")
    else:
        table.add_row("Settings.json", "[red]Not configured[/red]", f"Run: {install_cmd}")

    # Current profile
    table.add_row("Active profile", f"[cyan]{current_profile}[/cyan]", "CLAUDE_PROFILE or default")

    console.print(table)

    if installed_profiles:
        profiles_list = ", ".join(sorted(installed_profiles.keys()))
        console.print(f"\n[dim]Installed profiles: {profiles_list}[/dim]")


@app.command("default")
def manage_default(
    name: Annotated[str | None, typer.Argument(help="Profile name to set as default")] = None,
    clear: Annotated[
        bool, typer.Option("--clear", "-c", help="Clear default (use 'default' profile)")
    ] = False,
):
    """Get or set the default permission profile."""
    console = Console()

    if clear:
        if DEFAULT_PROFILE_FILE.exists():
            DEFAULT_PROFILE_FILE.unlink()
            console.print("[green]Cleared default profile (will use 'default')[/green]")
        else:
            console.print("[dim]No default profile was set[/dim]")
        return

    if name is None:
        # Show current default
        current = get_current_profile()
        import os

        if os.environ.get("CLAUDE_PROFILE"):
            console.print(f"Active profile: [cyan]{current}[/cyan] (from CLAUDE_PROFILE env var)")
        elif DEFAULT_PROFILE_FILE.exists():
            console.print(f"Default profile: [cyan]{current}[/cyan]")
            console.print(f"[dim]Set in: {DEFAULT_PROFILE_FILE}[/dim]")
        else:
            console.print(f"Default profile: [cyan]{current}[/cyan] (built-in default)")
        return

    # Validate profile exists
    installed = get_installed_profiles()
    bundled = get_bundled_profiles()

    if name not in installed and name not in bundled:
        rprint(f"[red]Profile '{name}' not found[/red]")
        available = ", ".join(sorted(set(installed.keys()) | set(bundled.keys())))
        rprint(f"[dim]Available: {available}[/dim]")
        raise typer.Exit(1)

    if name not in installed:
        rprint(f"[yellow]Warning: Profile '{name}' is bundled but not installed[/yellow]")
        rprint("[dim]Run: asutils claude permission install[/dim]")

    # Set default
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_PROFILE_FILE.write_text(name + "\n")
    console.print(f"[green]Set default profile to '{name}'[/green]")
    console.print(f"[dim]Saved to: {DEFAULT_PROFILE_FILE}[/dim]")


@app.command("uninstall")
def uninstall_profiles(
    keep_profiles: Annotated[
        bool, typer.Option("--keep-profiles", "-k", help="Keep profile files (only remove hook)")
    ] = False,
):
    """Remove permission hook configuration."""
    console = Console()

    # Remove from settings.json
    if CLAUDE_SETTINGS.exists():
        try:
            settings = json.loads(CLAUDE_SETTINGS.read_text())
            if "hooks" in settings and "PermissionRequest" in settings["hooks"]:

                def has_our_hook(hook_entry):
                    # New format: {"matcher": {...}, "hooks": [...]}
                    if "hooks" in hook_entry:
                        return any(
                            HOOK_FILENAME in h.get("command", "")
                            for h in hook_entry.get("hooks", [])
                        )
                    # Old format: {"type": "command", "command": "..."}
                    return HOOK_FILENAME in hook_entry.get("command", "")

                original_len = len(settings["hooks"]["PermissionRequest"])
                settings["hooks"]["PermissionRequest"] = [
                    h
                    for h in settings["hooks"]["PermissionRequest"]
                    if not has_our_hook(h)
                ]
                if len(settings["hooks"]["PermissionRequest"]) < original_len:
                    CLAUDE_SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
                    console.print("[green]Removed hook from settings.json[/green]")
                else:
                    console.print("[dim]Hook not found in settings.json[/dim]")
        except json.JSONDecodeError:
            console.print("[yellow]Could not parse settings.json[/yellow]")

    # Remove hook file
    hook_path = CLAUDE_HOOKS_DIR / HOOK_FILENAME
    if hook_path.exists():
        hook_path.unlink()
        console.print(f"[green]Removed {hook_path}[/green]")

    # Remove default profile file
    if DEFAULT_PROFILE_FILE.exists():
        DEFAULT_PROFILE_FILE.unlink()
        console.print("[green]Removed default profile setting[/green]")

    if not keep_profiles:
        # Remove profiles
        installed = get_installed_profiles()
        if installed:
            for name, path in installed.items():
                path.unlink()
                console.print(f"[green]Removed profile '{name}'[/green]")
            # Try to remove empty directory
            try:
                CLAUDE_PROFILES_DIR.rmdir()
            except OSError:
                pass  # Directory not empty (user has custom files)
    else:
        console.print(f"[dim]Profiles kept in {CLAUDE_PROFILES_DIR}[/dim]")

    console.print("\n[bold]Uninstall complete[/bold]")


if __name__ == "__main__":
    app()
