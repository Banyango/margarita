import re

from margarita.agent.core.agents.models import ExecutionModel, InputRequest
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin
from margarita.agent.entities.run import ContentBlock, ContentBlockType


class InputPlugin(AgentPlugin):
    def is_match(self, token: str) -> bool:
        return token == "input"

    async def handle(self, params: str, execution_model: ExecutionModel):
        match = re.match(r'^"(.*?)"\s*=>\s*(\w+)$', params.strip())
        if not match:
            raise ValueError(
                f"Invalid input syntax: '{params}'. Expected: \"prompt text\" => variable_name"
            )

        prompt_text = match.group(1)
        variable_name = match.group(2)

        prompt_text = execution_model.context.replace_variables_in_content(prompt_text)

        if execution_model.current_run:
            execution_model.current_run.content_blocks.append(
                ContentBlock(
                    type=ContentBlockType.QUESTION,
                    text=prompt_text,
                )
            )

        # Post a request for the UI to handle, then wait until it is resolved.
        request = InputRequest(prompt=prompt_text)
        await execution_model.request_input(request)
        user_input = request.response or ""

        execution_model.context.set_variable(variable_name, user_input)

        if execution_model.current_run:
            execution_model.current_run.content_blocks.append(
                ContentBlock(
                    type=ContentBlockType.LOGGING, text=f"[Input] {prompt_text}: {user_input}"
                )
            )
