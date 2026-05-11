import click

from margarita.agent.app.config import AppConfig, save_app_config
from margarita.agent.app.container import container
from margarita.agent.app.lifecycle import with_lifecycle
from margarita.agent.core.agents.models import ModelBackend


@click.command()
@click.argument(
    "model", type=click.Choice(["copilot", "ollama", "openai", "claude"], case_sensitive=False)
)
@with_lifecycle
async def use(model: str) -> None:
    config = await container.get(AppConfig)

    if model == "copilot":
        config.backend = ModelBackend.COPILOT
    elif model == "ollama":
        config.backend = ModelBackend.OLLAMA
    elif model == "openai":
        config.backend = ModelBackend.OPENAI
    elif model == "claude":
        config.backend = ModelBackend.CLAUDE
    else:
        raise click.BadParameter("Invalid model type")

    click.echo(f"Switched to {model} backend")

    save_app_config(config)
