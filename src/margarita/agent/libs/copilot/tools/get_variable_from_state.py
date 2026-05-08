from copilot import define_tool
from pydantic import BaseModel

from margarita.agent.core.agents.models import ExecutionModel


class GetVariableFromState(BaseModel):
    """Pydantic model for the get_variable tool parameters.

    Used by the Copilot tools layer to request variables from the agent state.
    """
    variable: str


async def create_get_variable_tool(execution_model: ExecutionModel):
    @define_tool(description="Get a variable from the shared state", skip_permission=True)
    async def get_variable(params: GetVariableFromState) -> dict:
        value = execution_model.context.get_variable_value(params.variable)
        return {params.variable: value}

    return get_variable
