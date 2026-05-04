import re

from margarita.agent.core.agents.models import ExecutionModel, InputRequest
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin
from margarita.agent.entities.content_block import ContentBlock
from margarita.agent.entities.run import ContentBlockType


class InputPlugin(AgentPlugin):
    def is_match(self, token: str) -> bool:
        return token == "input"

    async def handle_async(self, params: str, execution_model: ExecutionModel):
        stripped = params.strip()
        prompt_match = re.match(r'^"(.*?)"\s*=>\s*(\w+)$', stripped)
        silent_match = re.match(r"^=>\s*(\w+)$", stripped)

        if prompt_match:
            prompt_text = prompt_match.group(1)
            variable_name = prompt_match.group(2)
            prompt_text = execution_model.context.replace_variables_in_content(prompt_text)
        elif silent_match:
            prompt_text = None
            variable_name = silent_match.group(1)
        else:
            raise ValueError(
                f"Invalid input syntax: '{params}'. Expected: \"prompt text\" => variable_name  or  => variable_name"
            )

        if prompt_text is not None:
            execution_model.add_content_block(
                ContentBlock(
                    type=ContentBlockType.QUESTION,
                    text=prompt_text,
                )
            )

        # Post a request for the UI to handle, then wait until it is resolved.
        request = InputRequest(prompt=prompt_text or "")

        await execution_model.request_input(request)

        user_input = request.response or ""
        execution_model.context.set_variable(variable_name, user_input)

        log_text = (
            f"[Input] {prompt_text}: {user_input}" if prompt_text else f"[Input] {user_input}"
        )
        execution_model.add_content_block(
            ContentBlock(type=ContentBlockType.LOGGING, text=log_text)
        )
