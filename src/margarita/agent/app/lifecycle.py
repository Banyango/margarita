import asyncio
from contextlib import asynccontextmanager
from functools import wraps

from margarita.agent.app.container import container
from margarita.agent.libs.container import shutdown, startup


@asynccontextmanager
async def app_lifecycle():
    """Context manager for application lifecycle (startup/shutdown).

    Ensures proper initialization and cleanup of resources.
    """
    await startup(container)
    try:
        yield
    finally:
        await shutdown(container)


def with_lifecycle(func):
    """Decorator that wraps an async function with the app lifecycle context manager.

    Args:
        func: The async function to wrap.

    Returns:
        A wrapped function that runs with app lifecycle management.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        async def async_wrapper():
            async with app_lifecycle():
                return await func(*args, **kwargs)

        return asyncio.run(async_wrapper())

    return wrapper
