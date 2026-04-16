from wireup import AsyncContainer

from margarita.agent.libs.copilot.client import GithubCopilotClient


async def startup(container: AsyncContainer):
    """Initialize and connect the Copilot client.

    Args:
        container (AsyncContainer): The dependency injection container to retrieve the CopilotClient instance.
    """
    client = await container.get(GithubCopilotClient)
    await client.connect()


async def shutdown(container: AsyncContainer):
    """Disconnect the Copilot client.

    Args:
        container (AsyncContainer): The dependency injection container to retrieve the CopilotClient instance.
    """
    client = await container.get(GithubCopilotClient)
    await client.disconnect()
