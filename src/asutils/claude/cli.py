"""Claude Code utilities CLI."""

import typer

from asutils.claude import skill

app = typer.Typer(name="claude", help="Claude Code utilities")
app.add_typer(skill.app, name="skill")

if __name__ == "__main__":
    app()
