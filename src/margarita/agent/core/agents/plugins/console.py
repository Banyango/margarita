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

        # If start_run above failed due to awkward annotation logic fallback to creating Run via Run class
        try:
            self.logger_service.print(f"[Log.Info] {final_string}")
            execution_model.current_run.content_blocks.append(
                ContentBlock(type=ContentBlockType.LOGGING, text=final_string)
            )
        except Exception:
            # Last-resort: append to turns[-1].run.content_blocks if possible
            if execution_model.turns and execution_model.turns[-1].run is not None:
                execution_model.turns[-1].run.content_blocks.append(
                    ContentBlock(type=ContentBlockType.LOGGING, text=final_string)
                )
            else:
                # Cannot record output into run; print to stdout for harness capture as fallback
                print(final_string)
