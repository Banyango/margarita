from dataclasses import asdict

from margarita_open_agent.core.interfaces import PermissionCallbackHandler
from margarita_open_agent.core.models.permissions import PermissionsRequest

from margarita.agent import ExecutionModel
from margarita.agent.app.config import AppConfig
from margarita.agent.core.agents.models import PermissionPrompt

_INTERNAL_TOOLS = {"get_variable", "set_variable"}


class OpenAgentPermissionHandler(PermissionCallbackHandler):
    def __init__(self, execution_model: ExecutionModel, app_config: AppConfig):
        self.execution_model = execution_model
        self.app_config = app_config

    async def __call__(self, request: PermissionsRequest) -> bool:
        if self.app_config.ignore_permissions:
            return True

        if request.tool_name in _INTERNAL_TOOLS:
            return True

        prompt = PermissionPrompt(kind=request.kind.value, details=asdict(request))

        await self.execution_model.request_permission(prompt)

        return bool(prompt.approved)
