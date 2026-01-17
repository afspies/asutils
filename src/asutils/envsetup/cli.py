"""Environment setup CLI for asutils."""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Environment configuration utilities")

# Marker for idempotent config blocks
ASUTILS_MARKER_START = "# >>> asutils env config >>>"
ASUTILS_MARKER_END = "# <<< asutils env config <<<"


def get_default_shell() -> str:
    """Detect the user's default shell."""
    # Check SHELL env var first
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return "zsh"
    if "bash" in shell:
        return "bash"

    # Fall back to platform defaults
    if platform.system() == "Darwin":
        return "zsh"
    return "bash"


def get_shell_rc_path(shell: str) -> Path:
    """Get the RC file path for a shell."""
    home = Path.home()
    if shell == "zsh":
        return home / ".zshrc"
    return home / ".bashrc"


def is_command_available(cmd: str) -> bool:
    """Check if a command is available in PATH."""
    return shutil.which(cmd) is not None


def read_file_safe(path: Path) -> str:
    """Read file contents, return empty string if not exists."""
    if path.exists():
        return path.read_text()
    return ""


def add_config_block(path: Path, block: str, console: Console) -> bool:
    """Add a config block to a file, replacing existing asutils block if present.

    Returns True if changes were made.
    """
    content = read_file_safe(path)

    # Check if marker already exists
    if ASUTILS_MARKER_START in content:
        # Replace existing block
        import re

        pattern = rf"{re.escape(ASUTILS_MARKER_START)}.*?{re.escape(ASUTILS_MARKER_END)}"
        new_content = re.sub(pattern, block, content, flags=re.DOTALL)
        if new_content != content:
            path.write_text(new_content)
            console.print(f"  [yellow]Updated[/yellow] {path}")
            return True
        else:
            console.print(f"  [dim]No changes needed[/dim] {path}")
            return False
    else:
        # Append new block
        new_content = content.rstrip() + "\n\n" + block + "\n"
        path.write_text(new_content)
        console.print(f"  [green]Added config to[/green] {path}")
        return True


def generate_shell_config() -> str:
    """Generate shell configuration block."""
    lines = [ASUTILS_MARKER_START]

    # Claude Code aliases
    lines.append("")
    lines.append("# Claude Code aliases")
    lines.append("alias cc='claude'")
    lines.append("alias ccc='claude --continue'")

    # Claude Gateway aliases (only if installed)
    if is_command_available("claude-gateway"):
        lines.append("")
        lines.append("# Claude Gateway aliases")
        lines.append("alias cg='claude-gateway'")
        lines.append("alias cgc='claude-gateway --continue'")

    lines.append("")
    lines.append(ASUTILS_MARKER_END)

    return "\n".join(lines)


def generate_tmux_config() -> str:
    """Generate tmux configuration block."""
    lines = [
        ASUTILS_MARKER_START,
        "",
        "# Allow programs to rename windows",
        "set -g allow-rename on",
        "setw -g automatic-rename on",
        "",
        "# Window title format: basename of current path",
        "# Programs like Claude Code can override with escape sequences",
        "setw -g automatic-rename-format '#{b:pane_current_path}'",
        "",
        "# Set terminal title (shows in terminal tab)",
        "set -g set-titles on",
        "set -g set-titles-string '#{b:pane_current_path} - #{pane_title}'",
        "",
        ASUTILS_MARKER_END,
    ]
    return "\n".join(lines)


@app.command("setup")
def setup_env(
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing configuration")
    ] = False,
    shell: Annotated[
        str | None,
        typer.Option("--shell", "-s", help="Shell to configure (zsh/bash/auto)"),
    ] = None,
    skip_tmux: Annotated[
        bool, typer.Option("--skip-tmux", help="Skip tmux configuration")
    ] = False,
):
    """Set up environment configuration (aliases, tmux, etc.)."""
    console = Console()

    console.print(Panel("[bold]asutils Environment Setup[/bold]"))
    console.print()

    changes_made = []

    # Determine which shell to configure
    if shell is None or shell == "auto":
        detected_shell = get_default_shell()
        console.print(f"[dim]Detected shell:[/dim] {detected_shell}")
    else:
        detected_shell = shell

    # Configure shell
    console.print("\n[bold]Shell Configuration[/bold]")
    shell_rc = get_shell_rc_path(detected_shell)
    shell_config = generate_shell_config()

    if add_config_block(shell_rc, shell_config, console):
        changes_made.append(f"Shell config ({shell_rc.name})")

    # Show what aliases were added
    console.print("\n  [dim]Aliases configured:[/dim]")
    console.print("    cc  -> claude")
    console.print("    ccc -> claude --continue")
    if is_command_available("claude-gateway"):
        console.print("    cg  -> claude-gateway")
        console.print("    cgc -> claude-gateway --continue")
    else:
        console.print("    [dim](claude-gateway not found, skipping cg/cgc)[/dim]")

    # Configure tmux if available
    if not skip_tmux and is_command_available("tmux"):
        console.print("\n[bold]Tmux Configuration[/bold]")
        tmux_conf = Path.home() / ".tmux.conf"
        tmux_config = generate_tmux_config()

        if add_config_block(tmux_conf, tmux_config, console):
            changes_made.append("Tmux config")

        console.print("\n  [dim]Tmux settings:[/dim]")
        console.print("    allow-rename on")
        console.print("    automatic-rename on")
    elif not skip_tmux:
        console.print("\n[dim]Tmux not found, skipping tmux configuration[/dim]")

    # Summary
    console.print()
    if changes_made:
        console.print(Panel(f"[green]Setup complete![/green] Modified: {', '.join(changes_made)}"))
        console.print(f"\n[yellow]Restart your shell or run:[/yellow] source {shell_rc}")
    else:
        console.print(Panel("[dim]No changes needed - already configured[/dim]"))


@app.command("status")
def show_status():
    """Show current environment configuration status."""
    console = Console()

    table = Table(title="Environment Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    # Check shell config
    for shell in ["zsh", "bash"]:
        rc_path = get_shell_rc_path(shell)
        if rc_path.exists():
            content = rc_path.read_text()
            if ASUTILS_MARKER_START in content:
                table.add_row(f"{shell} config", "[green]Configured[/green]", str(rc_path))
            else:
                table.add_row(f"{shell} config", "[yellow]Not configured[/yellow]", str(rc_path))
        else:
            table.add_row(f"{shell} config", "[dim]File not found[/dim]", str(rc_path))

    # Check tmux
    tmux_conf = Path.home() / ".tmux.conf"
    if is_command_available("tmux"):
        if tmux_conf.exists():
            content = tmux_conf.read_text()
            if ASUTILS_MARKER_START in content:
                table.add_row("tmux config", "[green]Configured[/green]", str(tmux_conf))
            else:
                table.add_row("tmux config", "[yellow]Not configured[/yellow]", str(tmux_conf))
        else:
            table.add_row("tmux config", "[yellow]Not configured[/yellow]", "~/.tmux.conf not found")
    else:
        table.add_row("tmux", "[dim]Not installed[/dim]", "")

    # Check commands
    for cmd, desc in [
        ("claude", "Claude Code"),
        ("claude-gateway", "Claude Gateway"),
    ]:
        if is_command_available(cmd):
            table.add_row(desc, "[green]Available[/green]", shutil.which(cmd) or "")
        else:
            table.add_row(desc, "[dim]Not found[/dim]", "")

    console.print(table)


@app.command("uninstall")
def uninstall_env():
    """Remove asutils environment configuration."""
    console = Console()

    console.print("[bold]Removing asutils environment configuration...[/bold]\n")

    import re

    removed = []

    # Remove from shell configs
    for shell in ["zsh", "bash"]:
        rc_path = get_shell_rc_path(shell)
        if rc_path.exists():
            content = rc_path.read_text()
            if ASUTILS_MARKER_START in content:
                pattern = rf"\n*{re.escape(ASUTILS_MARKER_START)}.*?{re.escape(ASUTILS_MARKER_END)}\n*"
                new_content = re.sub(pattern, "\n", content, flags=re.DOTALL)
                rc_path.write_text(new_content)
                console.print(f"[green]Removed config from[/green] {rc_path}")
                removed.append(rc_path.name)

    # Remove from tmux.conf
    tmux_conf = Path.home() / ".tmux.conf"
    if tmux_conf.exists():
        content = tmux_conf.read_text()
        if ASUTILS_MARKER_START in content:
            pattern = rf"\n*{re.escape(ASUTILS_MARKER_START)}.*?{re.escape(ASUTILS_MARKER_END)}\n*"
            new_content = re.sub(pattern, "\n", content, flags=re.DOTALL)
            tmux_conf.write_text(new_content)
            console.print(f"[green]Removed config from[/green] {tmux_conf}")
            removed.append("tmux.conf")

    if removed:
        console.print(f"\n[bold]Removed configuration from:[/bold] {', '.join(removed)}")
    else:
        console.print("[dim]No asutils configuration found to remove[/dim]")


if __name__ == "__main__":
    app()
