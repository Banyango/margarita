from wireup import injectable

from margarita.agent import ExecutionModel
from margarita.agent.app.config import AppConfig
from margarita.agent.core.interfaces.logger import LoggerService
from margarita.agent.core.interfaces.query_service import QueryService
from margarita.agent.libs.open_agent.agent import OpenAgent


@injectable(as_type=QueryService, qualifier="openai")
class OpenAIAgent(QueryService):
    def __init__(self, app_config: AppConfig | None = None, logger: LoggerService | None = None):
        self.agent = OpenAgent(backend="openai", app_config=app_config, logger=logger)

    async def clear_session(self):
        pass

    async def execute_query(self, execution_model: ExecutionModel, params: str) -> str:
        return await self.agent.execute_query_async(execution_model=execution_model, params=params)
