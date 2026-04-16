from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin


class ContextPlugin(AgentPlugin):
    """Plugin for manipulating the agent execution context.

    Supports operations like clearing the context window or resetting state
    variables as requested by @effect context commands.
    """

    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.
        """
        return token == "context"

    async def handle(self, params: str, execution_model: ExecutionModel):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
        if params.lower() == "clear":
            execution_model.context.clear_context()
