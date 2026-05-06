from margarita_open_agent.core.models.tool import ToolDefinition, ToolFunction, ToolParameters

from margarita.agent.entities.tool import Tool


def convert_core_tool_to_open_agent(tool: list[Tool]) -> list[ToolDefinition]:
    """Convert a list of Tool objects to a list of ToolDefinition objects for Margarita Open Agent API."""
    tool_definitions = []
    for t in tool:
        tool_definitions.append(
            ToolDefinition(
                type="function",
                function=ToolFunction(
                    name=t.name,
                    description=t.description,
                    parameters=ToolParameters(
                        type="object",
                        properties={
                            param.name: {
                                "type": param.type,
                                "name": param.name,
                            }
                            for param in t.params
                        },
                        required=[param.name for param in t.params if param.required],
                    ),
                ),
            )
        )

    return tool_definitions
