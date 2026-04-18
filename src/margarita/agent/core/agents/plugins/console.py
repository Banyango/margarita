from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin
from margarita.agent.core.interfaces.logger import LoggerService
from margarita.agent.entities.run import ContentBlock, ContentBlockType


class ConsoleLogPlugin(AgentPlugin):
    def __init__(self, logger_service: LoggerService):
        super().__init__()
        self.logger_service = logger_service

    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.
        """
        return token == "log"

    async def handle(self, params: str, execution_model: ExecutionModel):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
        final_string = execution_model.context.replace_variables_in_content(params)

        self.logger_service.print(f"[Log.Info] {final_string}")

        # Find the most recent active run to record the log message.
        # current_run can be None after a @effect run causes start_turn() to create a new empty turn.
        target_run = execution_model.current_run
        if target_run is None:
            for turn in reversed(execution_model.turns):
                if turn.run is not None:
                    target_run = turn.run
                    break

        if target_run is not None:
            target_run.content_blocks.append(
                ContentBlock(type=ContentBlockType.LOGGING, text=final_string)
            )
        else:
            print(final_string)
