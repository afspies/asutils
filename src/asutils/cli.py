import typer

from asutils import git, publish, repo
from asutils.claude import cli as claude_cli
from asutils.envsetup import cli as env_cli

app = typer.Typer(name="asutils", help="Personal dev utilities")
app.add_typer(repo.app, name="repo")
app.add_typer(publish.app, name="publish")
app.add_typer(git.app, name="git")
app.add_typer(claude_cli.app, name="claude")
app.add_typer(env_cli.app, name="env")


@app.command("setup")
def setup(
    profile: str = typer.Option("dev", "--profile", "-p", help="Permission profile"),
    skill_bundle: str = typer.Option("default", "--skills", "-s", help="Skill bundle"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing"),
):
    """Quick setup for Claude Code (alias for 'asutils claude setup')."""
    claude_cli.setup(profile=profile, skill_bundle=skill_bundle, force=force)


if __name__ == "__main__":
    app()
