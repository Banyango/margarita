from margarita_open_agent.core.interfaces import UserInputCallbackHandler
from margarita_open_agent.core.models.permissions import UserInputRequest

from margarita.agent import ContentBlock, ContentBlockType, ExecutionModel
from margarita.agent.core.agents.models import InputRequest


class OpenAgentUserInputHandler(UserInputCallbackHandler):
    def __init__(self, execution_model: ExecutionModel):
        self.execution_model = execution_model

    async def __call__(self, request: UserInputRequest) -> str:
        response = f"[Question] {request.question}"

        self.execution_model.current_run.content_blocks.append(
            ContentBlock(
                type=ContentBlockType.INPUT,
                ref="",
                text=response,
            )
        )

        request = InputRequest(prompt=request.question)

        await self.execution_model.request_input(request)

        return request.response or ""
