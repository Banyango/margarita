from margarita_open_agent.core.interfaces import UserToolCallbackHandler
from margarita_open_agent.core.models.tool import (
    ToolCallRequest,
    ToolDefinition,
    ToolFunction,
    ToolParameters,
)

from margarita.agent import ExecutionModel

GET_TOOL_DEFINITION: ToolDefinition = ToolDefinition(
    type="function",
    function=ToolFunction(
        name="get_variable",
        description="Get a variable from the shared state. When you don't have a variable use this to get it.",
        parameters=ToolParameters(
            type="object",
            properties={
                "variable": {
                    "type": "string",
                    "description": "The the variable name to get.",
                }
            },
        ),
    ),
)

SET_TOOL_DEFINITION: ToolDefinition = ToolDefinition(
    type="function",
    function=ToolFunction(
        name="set_variable",
        description="Set a variable in the shared state, for putting it in a var",
        parameters=ToolParameters(
            type="object",
            properties={
                "name": {
                    "type": "string",
                    "description": "The the variable name to set.",
                },
                "value": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "integer"},
                        {"type": "number"},
                        {"type": "boolean"},
                        {"type": "array"},
                        {"type": "object"},
                        {"type": "null"},
                    ],
                    "description": "The value to set.",
                },
            },
        ),
    ),
)


class OpenAgentCustomToolHandler(UserToolCallbackHandler):
    def __init__(self, execution_model: ExecutionModel) -> None:
        self.execution_model = execution_model

    async def __call__(self, request: ToolCallRequest) -> str:
        if request["name"] == "get_variable":
            return self.execution_model.context.get_variable_value(
                request["arguments"].get("variable", "")
            )
        elif request["name"] == "set_variable":
            var = request["arguments"]["name"]
            return self.execution_model.context.set_variable(var, request["arguments"]["value"])
        else:
            return ""
