from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from copilot import CopilotClient, CopilotSession
from copilot.generated.session_events import PermissionRequest
from copilot.session import (
    InfiniteSessionConfig,
    PermissionRequestResult,
    SystemMessageConfig,
    UserInputHandler,
)
from copilot.tools import Tool
from wireup import injectable


@dataclass
class SessionConfig:
    client_name = "MargaritaAI"
    model: str
    streaming: bool
    on_permission_request: Callable[
        [PermissionRequest, dict[str, str]],
        PermissionRequestResult | Awaitable[PermissionRequestResult],
    ]
    infinite_sessions: bool
    tools: list[Tool]
    system_message: SystemMessageConfig | None = None
    on_user_input_request: UserInputHandler | None = None


@injectable
class GithubCopilotClient:
    """Wrapper around the GitHub Copilot SDK client used by the adapter.

    Provides convenience methods for opening sessions, sending events, and
    translating SDK errors into the project's error types.
    """

    def __init__(self):
        self.con: CopilotClient | None = None
        self.session: CopilotSession | None = None

    async def connect(self):
        self.con = CopilotClient()
        await self.con.start()

    async def disconnect(self):
        if self.con:
            await self.con.force_stop()

    async def create_session(self, session_config: SessionConfig):
        if not self.con:
            raise RuntimeError("Copilot client is not connected")

        self.session = await self.con.create_session(
            client_name=session_config.client_name,
            system_message=session_config.system_message,
            model=session_config.model,
            streaming=session_config.streaming,
            on_permission_request=session_config.on_permission_request,
            infinite_sessions=InfiniteSessionConfig(enabled=session_config.infinite_sessions),
            tools=session_config.tools,
            on_user_input_request=session_config.on_user_input_request,
        )

    async def destroy_current_session(self):
        if not self.con:
            raise RuntimeError("Copilot client is not connected")

        await self.session.destroy()
        self.session = None
