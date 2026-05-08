from mcp.types import ToolAnnotations
from pydantic import BaseModel

from claude_agent_sdk import SdkMcpTool

from margarita.agent.core.agents.models import ExecutionModel


class GetVariableParams(BaseModel):
    name: str


def create_get_variable_tool(execution_model: ExecutionModel) -> SdkMcpTool:
    async def handler(params: GetVariableParams) -> dict:
        value = execution_model.context.get_variable_value(params["name"])
        return {"content": [{"type": "text", "text": str({params["name"]: value})}]}

    return SdkMcpTool(
        name="get_variable",
        description="Get a variable from the shared state",
        input_schema=GetVariableParams.model_json_schema(),
        handler=handler,
        annotations=ToolAnnotations(title="Get a variable from the shared state", readOnlyHint=True)
    )
