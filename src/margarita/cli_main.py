from importlib.metadata import version

import click

from margarita.agent.app.cli.agents.run import run
from margarita.agent.app.cli.prompts.commands import prompts
from margarita.language.cli import install_claude_skill, render


@click.group()
@click.version_option(version=version("margarita"), prog_name="margarita")
def cli():
    """Margarita - A tool for executing .mgx files and managing agents."""
    pass


cli.add_command(run)
cli.add_command(prompts)
cli.add_command(install_claude_skill)
cli.add_command(render)

if __name__ == "__main__":
    cli()
