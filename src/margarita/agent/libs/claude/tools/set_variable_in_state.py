from claude_agent_sdk import SdkMcpTool
from pydantic import BaseModel

from margarita.agent.core.agents.models import ExecutionModel


class SetVariableParams(BaseModel):
    name: str
    value: str | list | dict | int | float | bool | None


def create_set_variable_tool(execution_model: ExecutionModel) -> SdkMcpTool:
    async def handler(params: SetVariableParams) -> dict:
        execution_model.set_variable(params["name"], params["value"])
        return {"content": [{"type": "text", "text": str({"value": params["value"]})}]}

    return SdkMcpTool(
        name="set_variable",
        description="Set a variable in the shared state",
        input_schema=SetVariableParams.model_json_schema(),
        handler=handler,
    )
