"""Claude Code utilities CLI."""

import typer

from asutils.claude import skill
from asutils.claude.permissions import cli as permission

app = typer.Typer(name="claude", help="Claude Code utilities")
app.add_typer(skill.app, name="skill")
app.add_typer(permission.app, name="permission")

if __name__ == "__main__":
    app()
