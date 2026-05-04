import re

from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin
from margarita.agent.entities.tool import Param, Tool


class ToolsPlugin(AgentPlugin):
    """Registers tools that the LLM can call during a run.

    ToolsPlugin exposes tool metadata to the Copilot client so the model can
    execute functions via the tool interface.
    """

    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.
        """
        return token == "tools"

    async def handle_async(self, params: str, execution_model: ExecutionModel):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
        pattern = re.compile(r"^\s*([A-Za-z_]\w*)\s*\(\s*(.*?)\s*\)\s*(?:=>\s*(.+))?\s*$")
        match = pattern.match(params)

        if not match:
            if params == "clear":
                execution_model.context.tools = []
            return

        parameters = []

        func_name = match.group(1)
        func_params_str = match.group(2)
        result_var = match.group(3)

        if func_name not in execution_model.globals_dict:
            return

        if func_params_str:
            for p in func_params_str.split(","):
                ptype = p.split(":")[1].replace(" ", "")
                name = p.split(":")[0].replace(" ", "")
                parameters.append(Param(name=name, type=ptype))

        result_types = []
        if result_var:
            result_types = result_var.split(",")
            result_types = [r.strip() for r in result_types]

        execution_model.context.add_tool(
            Tool(name=func_name, params=parameters, return_types=result_types)
        )
