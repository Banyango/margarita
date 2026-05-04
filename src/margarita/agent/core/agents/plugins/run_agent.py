from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin
from margarita.agent.core.interfaces.query_service import QueryService


class RunAgentPlugin(AgentPlugin):
    """Plugin that executes LLM queries using a QueryService implementation.

    Translates @effect run tokens into calls to the configured QueryService and
    integrates streaming responses back into the execution model.
    """

    def __init__(self, agent_service: QueryService):
        super().__init__()
        self.agent_service = agent_service

    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.
        """
        return token == "run"

    async def handle_async(self, params: str, execution_model: ExecutionModel):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
        await self.agent_service.execute_query(execution_model=execution_model, params=params)
