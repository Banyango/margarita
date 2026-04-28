from wireup import AsyncContainer

from margarita.agent.app.config import AppConfig
from margarita.agent.core.agents.models import ModelBackend
from margarita.agent.libs.copilot.client import GithubCopilotClient


async def startup(container: AsyncContainer):
    """Initialize and connect the Copilot client.

    Args:
        container (AsyncContainer): The dependency injection container to retrieve the CopilotClient instance.
    """
    # todo fix me
    config = await container.get(AppConfig)

    if config.backend == ModelBackend.COPILOT:
        client = await container.get(GithubCopilotClient)
        await client.connect()


async def shutdown(container: AsyncContainer):
    """Disconnect the Copilot client.

    Args:
        container (AsyncContainer): The dependency injection container to retrieve the CopilotClient instance.
    """
    config = await container.get(AppConfig)

    if config.backend == ModelBackend.COPILOT:
        client = await container.get(GithubCopilotClient)
        await client.disconnect()
