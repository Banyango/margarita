from margarita.agent import ExecutionModel
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin


class StopPlugin(AgentPlugin):
    def is_match(self, token: str) -> bool:
        return token == "stop"

    async def handle(self, params: str, execution_model: ExecutionModel):
        execution_model.stop()
