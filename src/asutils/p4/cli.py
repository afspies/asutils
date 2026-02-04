"""CLI commands for Perforce exploration."""

import json
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from asutils.p4 import api, config

app = typer.Typer(name="p4", help="Explore Epic's Perforce depot")


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
