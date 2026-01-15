"""TTS CLI for Claude Code."""

import json
import tempfile
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Text-to-speech for Claude Code responses")

# Bundled files (alongside this module)
BUNDLED_STOP_HOOK = Path(__file__).parent / "hook.py"
BUNDLED_COMMAND = Path(__file__).parent / "commands" / "tts.md"

# Claude Code directories
CLAUDE_DIR = Path.home() / ".claude"
CLAUDE_HOOKS_DIR = CLAUDE_DIR / "hooks"
CLAUDE_COMMANDS_DIR = CLAUDE_DIR / "commands"
CLAUDE_SETTINGS = CLAUDE_DIR / "settings.json"
TTS_CONFIG_FILE = CLAUDE_DIR / "tts-config.yaml"

STOP_HOOK_FILENAME = "tts-hook.py"
COMMAND_FILENAME = "tts.md"


def load_config() -> dict:
    """Load TTS configuration."""
    config = {
        "voice": "Samantha",
        "rate": 175,
        "focus_window": True,
        "terminal_app": "auto",
        "always_enabled": False,
    }

    if TTS_CONFIG_FILE.exists():
        try:
            import yaml

            with open(TTS_CONFIG_FILE) as f:
                user_config = yaml.safe_load(f) or {}
                config.update(user_config)
        except Exception:
            pass

    return config


def save_config(config: dict) -> None:
    """Save TTS configuration."""
    import yaml

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    with open(TTS_CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def is_hook_installed() -> bool:
    """Check if the TTS Stop hook is installed in settings.json."""
    if not CLAUDE_SETTINGS.exists():
        return False
    try:
        settings = json.loads(CLAUDE_SETTINGS.read_text())
        hooks = settings.get("hooks", {})
        stop_hooks = hooks.get("Stop", [])
        for hook_entry in stop_hooks:
            if "hooks" in hook_entry:
                for h in hook_entry.get("hooks", []):
                    if STOP_HOOK_FILENAME in h.get("command", ""):
                        return True
            elif STOP_HOOK_FILENAME in hook_entry.get("command", ""):
                return True
    except (json.JSONDecodeError, KeyError):
        pass
    return False


def is_command_installed() -> bool:
    """Check if the /tts command is installed."""
    return (CLAUDE_COMMANDS_DIR / COMMAND_FILENAME).exists()


@app.command("install")
def install_hook(
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing files")
    ] = False,
):
    """Install TTS hook and /tts command to ~/.claude/."""
    console = Console()

    # Create directories
    CLAUDE_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    CLAUDE_COMMANDS_DIR.mkdir(parents=True, exist_ok=True)

    # Read existing settings
    if CLAUDE_SETTINGS.exists():
        try:
            settings = json.loads(CLAUDE_SETTINGS.read_text())
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}

    if "hooks" not in settings:
        settings["hooks"] = {}

    # Install Stop hook (reads responses aloud)
    console.print("[bold]Installing TTS Stop hook...[/bold]")
    stop_hook_target = CLAUDE_HOOKS_DIR / STOP_HOOK_FILENAME
    if stop_hook_target.exists() and not force:
        console.print(f"  [yellow]{STOP_HOOK_FILENAME} exists (use --force to overwrite)[/yellow]")
    else:
        stop_hook_target.write_text(BUNDLED_STOP_HOOK.read_text())
        stop_hook_target.chmod(0o755)
        console.print(f"  [green]Installed {stop_hook_target}[/green]")

    # Configure Stop hook in settings.json
    if "Stop" not in settings["hooks"]:
        settings["hooks"]["Stop"] = []

    def has_stop_hook(hook_entry):
        if "hooks" in hook_entry:
            return any(
                STOP_HOOK_FILENAME in h.get("command", "") for h in hook_entry.get("hooks", [])
            )
        return STOP_HOOK_FILENAME in hook_entry.get("command", "")

    stop_hook_exists = any(has_stop_hook(h) for h in settings["hooks"]["Stop"])

    if stop_hook_exists and not force:
        console.print("  [yellow]Stop hook already in settings.json[/yellow]")
    else:
        if force:
            settings["hooks"]["Stop"] = [
                h for h in settings["hooks"]["Stop"] if not has_stop_hook(h)
            ]
        stop_hook_command = f"python3 {stop_hook_target}"
        settings["hooks"]["Stop"].append(
            {"hooks": [{"type": "command", "command": stop_hook_command}]}
        )
        console.print("  [green]Configured Stop hook[/green]")

    # Save settings
    CLAUDE_SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")

    # Install /tts command
    console.print("\n[bold]Installing /tts command...[/bold]")
    command_target = CLAUDE_COMMANDS_DIR / COMMAND_FILENAME
    if command_target.exists() and not force:
        console.print(f"  [yellow]{COMMAND_FILENAME} exists (use --force to overwrite)[/yellow]")
    else:
        command_target.write_text(BUNDLED_COMMAND.read_text())
        console.print(f"  [green]Installed {command_target}[/green]")

    # Create default config if not exists
    if not TTS_CONFIG_FILE.exists():
        console.print("\n[bold]Creating default config...[/bold]")
        save_config(load_config())
        console.print(f"  [green]Created {TTS_CONFIG_FILE}[/green]")

    console.print("\n[bold green]Installation complete![/bold green]")
    console.print("\n[dim]Usage:[/dim]")
    console.print("  /tts                            # Toggle TTS for current session")
    console.print("  asutils claude tts enable --always  # Enable for all sessions")
    console.print("  asutils claude tts test 'Hello'     # Test TTS")


@app.command("uninstall")
def uninstall_hook():
    """Remove TTS hook and command from ~/.claude/."""
    console = Console()

    # Remove Stop hook from settings.json
    if CLAUDE_SETTINGS.exists():
        try:
            settings = json.loads(CLAUDE_SETTINGS.read_text())

            if "hooks" in settings and "Stop" in settings["hooks"]:

                def has_stop_hook(hook_entry):
                    if "hooks" in hook_entry:
                        return any(
                            STOP_HOOK_FILENAME in h.get("command", "")
                            for h in hook_entry.get("hooks", [])
                        )
                    return STOP_HOOK_FILENAME in hook_entry.get("command", "")

                original_len = len(settings["hooks"]["Stop"])
                settings["hooks"]["Stop"] = [
                    h for h in settings["hooks"]["Stop"] if not has_stop_hook(h)
                ]
                if len(settings["hooks"]["Stop"]) < original_len:
                    CLAUDE_SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
                    console.print("[green]Removed Stop hook from settings.json[/green]")
                else:
                    console.print("[dim]Stop hook not found in settings.json[/dim]")

        except json.JSONDecodeError:
            console.print("[yellow]Could not parse settings.json[/yellow]")

    # Remove hook file
    stop_hook_path = CLAUDE_HOOKS_DIR / STOP_HOOK_FILENAME
    if stop_hook_path.exists():
        stop_hook_path.unlink()
        console.print(f"[green]Removed {stop_hook_path}[/green]")

    # Remove command file
    command_path = CLAUDE_COMMANDS_DIR / COMMAND_FILENAME
    if command_path.exists():
        command_path.unlink()
        console.print(f"[green]Removed {command_path}[/green]")

    console.print("\n[bold]Uninstall complete[/bold]")


@app.command("toggle")
def toggle_tts():
    """Toggle TTS on/off for the current session."""
    tts_flag = Path(tempfile.gettempdir()) / "claude-tts-active"

    if tts_flag.exists():
        tts_flag.unlink()
        print("DISABLED")
    else:
        tts_flag.touch()
        print("ENABLED")


@app.command("enable")
def enable_tts(
    always: Annotated[
        bool, typer.Option("--always", "-a", help="Enable for all sessions (persistent)")
    ] = False,
):
    """Enable TTS. Use --always for persistent mode across all sessions."""
    console = Console()

    if always:
        config = load_config()
        config["always_enabled"] = True
        save_config(config)
        console.print("[green]TTS enabled for all sessions[/green]")
        console.print("[dim]Claude's responses will now be read aloud[/dim]")
    else:
        console.print(
            "[yellow]Session-based TTS requires the /tts command in Claude Code[/yellow]"
        )
        console.print("\n[dim]Options:[/dim]")
        console.print("  /tts                          # In Claude Code session")
        console.print("  asutils claude tts enable --always  # Persistent mode")


@app.command("disable")
def disable_tts():
    """Disable persistent TTS."""
    console = Console()

    config = load_config()
    config["always_enabled"] = False
    save_config(config)
    console.print("[green]Persistent TTS disabled[/green]")
    console.print("[dim]Use /tts in Claude Code to enable per-session[/dim]")


@app.command("status")
def show_status():
    """Show TTS installation and configuration status."""
    console = Console()

    stop_hook_installed = is_hook_installed()
    command_installed = is_command_installed()
    stop_hook_file_exists = (CLAUDE_HOOKS_DIR / STOP_HOOK_FILENAME).exists()
    config = load_config()

    fully_installed = stop_hook_installed and stop_hook_file_exists and command_installed

    # Overall status
    if fully_installed:
        if config.get("always_enabled"):
            console.print(Panel("[bold green]TTS installed and always enabled[/bold green]"))
        else:
            console.print(
                Panel("[bold cyan]TTS installed (use /tts or --always to enable)[/bold cyan]")
            )
    else:
        console.print(Panel("[bold yellow]TTS not fully installed[/bold yellow]"))

    console.print()

    # Details table
    table = Table(title="TTS Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    # Stop hook file
    if stop_hook_file_exists:
        table.add_row(
            "Stop hook",
            "[green]Installed[/green]",
            str(CLAUDE_HOOKS_DIR / STOP_HOOK_FILENAME),
        )
    else:
        table.add_row("Stop hook", "[red]Missing[/red]", "Run: asutils claude tts install")

    # /tts command
    if command_installed:
        table.add_row(
            "/tts command",
            "[green]Installed[/green]",
            str(CLAUDE_COMMANDS_DIR / COMMAND_FILENAME),
        )
    else:
        table.add_row("/tts command", "[red]Missing[/red]", "Run: asutils claude tts install")

    # Settings config
    if stop_hook_installed:
        table.add_row("Settings.json", "[green]Configured[/green]", "Stop hook registered")
    else:
        table.add_row(
            "Settings.json",
            "[red]Not configured[/red]",
            "Run: asutils claude tts install",
        )

    # Always enabled
    if config.get("always_enabled"):
        table.add_row("Mode", "[green]Always enabled[/green]", "All sessions")
    else:
        table.add_row("Mode", "[cyan]Per-session[/cyan]", "Use /tts to enable")

    # Voice
    table.add_row("Voice", f"[cyan]{config.get('voice', 'Samantha')}[/cyan]", "")

    # Rate
    table.add_row("Rate", f"[cyan]{config.get('rate', 175)} wpm[/cyan]", "")

    # Window focus
    focus = config.get("focus_window", True)
    if focus:
        app_name = config.get("terminal_app", "auto")
        table.add_row("Window focus", "[green]Enabled[/green]", f"App: {app_name}")
    else:
        table.add_row("Window focus", "[dim]Disabled[/dim]", "")

    console.print(table)

    if TTS_CONFIG_FILE.exists():
        console.print(f"\n[dim]Config file: {TTS_CONFIG_FILE}[/dim]")


@app.command("test")
def test_tts(
    text: Annotated[str, typer.Argument(help="Text to speak")] = "Hello! TTS is working.",
):
    """Test TTS by speaking the given text."""
    from asutils.claude.tts.speak import speak

    config = load_config()
    voice = config.get("voice", "Samantha")
    rate = config.get("rate", 175)

    rprint(f"[dim]Speaking with voice '{voice}' at {rate} wpm...[/dim]")
    speak(text, voice=voice, rate=rate)
    rprint("[green]Done![/green]")


@app.command("voices")
def list_voices():
    """List available macOS voices."""
    from asutils.claude.tts.speak import list_voices

    console = Console()
    voices = list_voices()

    if not voices:
        console.print("[yellow]No voices found (is this macOS?)[/yellow]")
        return

    config = load_config()
    current_voice = config.get("voice", "Samantha")

    table = Table(title="Available Voices")
    table.add_column("Voice", style="cyan")
    table.add_column("Current")

    for voice in voices:
        is_current = voice == current_voice
        table.add_row(voice, "[green]yes[/green]" if is_current else "")

    console.print(table)
    console.print(f"\n[dim]Set voice with: asutils claude tts config --voice NAME[/dim]")


@app.command("config")
def configure_tts(
    voice: Annotated[str | None, typer.Option("--voice", "-v", help="macOS voice name")] = None,
    rate: Annotated[int | None, typer.Option("--rate", "-r", help="Words per minute")] = None,
    focus: Annotated[
        bool | None, typer.Option("--focus/--no-focus", help="Focus terminal after speaking")
    ] = None,
    terminal: Annotated[
        str | None,
        typer.Option("--terminal", "-t", help="Terminal app (auto/Terminal/iTerm/none)"),
    ] = None,
):
    """Configure TTS settings."""
    console = Console()

    config = load_config()
    changed = False

    if voice is not None:
        config["voice"] = voice
        changed = True
        console.print(f"[green]Voice set to '{voice}'[/green]")

    if rate is not None:
        config["rate"] = rate
        changed = True
        console.print(f"[green]Rate set to {rate} wpm[/green]")

    if focus is not None:
        config["focus_window"] = focus
        changed = True
        console.print(f"[green]Window focus {'enabled' if focus else 'disabled'}[/green]")

    if terminal is not None:
        if terminal not in ("auto", "Terminal", "iTerm", "none"):
            rprint(f"[red]Invalid terminal: {terminal}[/red]")
            rprint("[dim]Valid options: auto, Terminal, iTerm, none[/dim]")
            raise typer.Exit(1)
        config["terminal_app"] = terminal
        changed = True
        console.print(f"[green]Terminal app set to '{terminal}'[/green]")

    if changed:
        save_config(config)
        console.print(f"\n[dim]Saved to {TTS_CONFIG_FILE}[/dim]")
    else:
        # Show current config
        console.print("[bold]Current TTS Configuration:[/bold]")
        console.print(f"  Voice: [cyan]{config.get('voice', 'Samantha')}[/cyan]")
        console.print(f"  Rate: [cyan]{config.get('rate', 175)} wpm[/cyan]")
        console.print(
            f"  Focus: [cyan]{'enabled' if config.get('focus_window', True) else 'disabled'}[/cyan]"
        )
        console.print(f"  Terminal: [cyan]{config.get('terminal_app', 'auto')}[/cyan]")
        console.print(
            f"  Always enabled: [cyan]{'yes' if config.get('always_enabled') else 'no'}[/cyan]"
        )
        console.print(f"\n[dim]Use --voice, --rate, --focus, --terminal to change[/dim]")


if __name__ == "__main__":
    app()
