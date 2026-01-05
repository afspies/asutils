import typer

from asutils import git, publish, repo
from asutils.claude import cli as claude_cli

app = typer.Typer(name="asutils", help="Personal dev utilities")
app.add_typer(repo.app, name="repo")
app.add_typer(publish.app, name="publish")
app.add_typer(git.app, name="git")
app.add_typer(claude_cli.app, name="claude")

if __name__ == "__main__":
    app()
