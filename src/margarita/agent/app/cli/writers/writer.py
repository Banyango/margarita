from typing import Any

from wireup import injectable

from margarita.agent.app.config import AppConfig
from margarita.agent.app.ui.app import Margarita
from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.core.interfaces.ui import UI


@injectable(as_type=UI)
class CliWriter(UI):
    def __init__(self, app_config: AppConfig):
        self.app_config = app_config
        self._tool_call_cache: dict[str, Any] = {}

    async def render_ui(self, execution_model: ExecutionModel):
        app = Margarita(execution_model=execution_model, app_config=self.app_config)
        await app.run_async()
