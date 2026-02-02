"""CLI commands for Confluence search and page retrieval."""

import json
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from asutils.confluence import api

app = typer.Typer(name="confluence", help="Search Epic's Confluence wiki")


@app.command("search")
def search_cmd(
    queries: Annotated[list[str], typer.Argument(help="Search queries")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="Max results per query")] = 10,
    space: Annotated[str | None, typer.Option("--space", "-s", help="Limit to space")] = None,
    parallel: Annotated[bool, typer.Option("--parallel", "-p", help="Run queries in parallel")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Search Confluence for pages matching query.

    Examples:
        asutils confluence search "deployment"
        asutils confluence search "auth" "login" "sso" --parallel
        asutils confluence search "API" --space DEV --limit 20
    """
    try:
        if parallel and len(queries) > 1:
            results = api.search_parallel(queries, limit, space)
        else:
            results = []
            for q in queries:
                results.extend(api.search(q, limit, space))

        if json_output:
            rprint(json.dumps(results, indent=2))
        else:
            _display_search_results(results, queries)

    except ValueError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Search failed:[/red] {e}")
        raise typer.Exit(1)


@app.command("page")
def get_page_cmd(
    page_id: Annotated[str, typer.Argument(help="Confluence page ID")],
    raw: Annotated[bool, typer.Option("--raw", "-r", help="Output raw HTML")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Get full content of a Confluence page.

    Examples:
        asutils confluence page 12345678
        asutils confluence page 12345678 --raw
    """
    try:
        page = api.get_page(page_id, as_markdown=not raw)

        if json_output:
            rprint(json.dumps(page, indent=2))
        else:
            rprint(f"[bold]# {page['title']}[/bold]\n")
            rprint(f"[dim]Space:[/dim] {page['space']} | [dim]URL:[/dim] {page['url']}\n")
            rprint("---\n")
            rprint(page["body"])

    except ValueError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Failed to get page:[/red] {e}")
        raise typer.Exit(1)


@app.command("spaces")
def list_spaces_cmd(
    limit: Annotated[int, typer.Option("--limit", "-l", help="Max spaces to show")] = 50,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List available Confluence spaces.

    Examples:
        asutils confluence spaces
        asutils confluence spaces --limit 100
    """
    try:
        spaces = api.list_spaces(limit)

        if json_output:
            rprint(json.dumps(spaces, indent=2))
        else:
            console = Console()
            table = Table(title="Confluence Spaces")
            table.add_column("Key", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Type", style="dim")

            for s in spaces:
                table.add_row(s["key"], s["name"], s["type"])

            console.print(table)

    except ValueError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Failed to list spaces:[/red] {e}")
        raise typer.Exit(1)


@app.command("cql")
def search_cql_cmd(
    cql: Annotated[str, typer.Argument(help="CQL query string")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="Max results")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Search Confluence using raw CQL (Confluence Query Language).

    Examples:
        asutils confluence cql 'text~"automation" AND space="DEV"'
        asutils confluence cql 'title~"guide" AND type=page'
        asutils confluence cql 'lastModified >= now("-7d")'
    """
    try:
        results = api.search_cql(cql, limit)

        if json_output:
            rprint(json.dumps(results, indent=2))
        else:
            _display_search_results(results, [cql])

    except ValueError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]CQL search failed:[/red] {e}")
        raise typer.Exit(1)


@app.command("children")
def get_children_cmd(
    parent_id: Annotated[str, typer.Argument(help="Parent page ID")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="Max children")] = 50,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Get child pages of a parent page.

    Examples:
        asutils confluence children 12345678
    """
    try:
        children = api.get_child_pages(parent_id, limit)

        if json_output:
            rprint(json.dumps(children, indent=2))
        else:
            console = Console()
            table = Table(title=f"Child Pages of {parent_id}")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")

            for c in children:
                table.add_row(c["id"], c["title"])

            console.print(table)
            rprint(f"\n[dim]Found {len(children)} child pages[/dim]")

    except ValueError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Failed to get children:[/red] {e}")
        raise typer.Exit(1)


def _display_search_results(results: list[dict], queries: list[str]) -> None:
    """Display search results in a formatted table."""
    console = Console()

    if not results:
        rprint(f"[yellow]No results found for: {', '.join(queries)}[/yellow]")
        return

    table = Table(title=f"Search Results ({len(results)} found)")
    table.add_column("Title", style="cyan", max_width=50)
    table.add_column("Space", style="magenta")
    table.add_column("Page ID", style="dim")
    table.add_column("Excerpt", style="white", max_width=60)

    for r in results:
        excerpt = r.get("excerpt", "")[:60]
        if len(r.get("excerpt", "")) > 60:
            excerpt += "..."
        table.add_row(
            r["title"],
            r.get("space", ""),
            r.get("page_id", ""),
            excerpt,
        )

    console.print(table)

    # Also print URLs for easy access
    rprint("\n[bold]URLs:[/bold]")
    for r in results[:10]:  # Limit URL output
        rprint(f"  - {r['title']}: {r['url']}")

    if len(results) > 10:
        rprint(f"  [dim]... and {len(results) - 10} more[/dim]")


if __name__ == "__main__":
    app()
