import typer

from asutils import git, publish, repo

app = typer.Typer(name="asutils", help="Personal dev utilities")
app.add_typer(repo.app, name="repo")
app.add_typer(publish.app, name="publish")
app.add_typer(git.app, name="git")

if __name__ == "__main__":
    app()
