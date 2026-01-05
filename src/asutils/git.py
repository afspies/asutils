"""Git utilities (placeholder for expansion)."""
import subprocess

import typer
from rich import print as rprint

app = typer.Typer(help="Git helpers")


@app.command("sync")
def sync(message: str = typer.Option("sync", "-m", help="Commit message")):
    """Quick add, commit, push."""
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)
    rprint("[green]✓[/] Synced")


@app.command("undo")
def undo():
    """Undo last commit, keep changes staged."""
    subprocess.run(["git", "reset", "--soft", "HEAD~1"], check=True)
    rprint("[green]✓[/] Undid last commit")


if __name__ == "__main__":
    app()
