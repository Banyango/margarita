import re

from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin


class FuncPlugin(AgentPlugin):
    """Plugin implementing the 'func' @effect which executes Python functions.

    The plugin runs allowed Python functions in the agent's execution context and
    stores results back into the execution model state.
    """

    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.
        """
        return token == "func"

    async def handle_async(self, params: str, execution_model: ExecutionModel):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
        params = params.strip()

        result = re.match(r"^(.*?)\s*=>\s*(.+)$", params)

        method_value = result.groups()[0]
        result_value = result.groups()[1] if len(result.groups()) > 1 else None

        match = re.search(r"([A-Za-z_][\w\.]*)\(\s*(.*?)\s*\)", method_value)
        func_param_str = match.groups()[1] if match and len(match.groups()) > 1 else None
        func_params = func_param_str.split(",") if func_param_str else []

        all_params = {}
        for param in func_params:
            key_stripped = param.replace(" ", "")
            value = execution_model.context.get_variable_value(key_stripped)
            if value:
                all_params[key_stripped] = value

        call = execution_model.add_function_call_log(method=method_value, params=all_params)

        try:
            results = eval(method_value, execution_model.globals_dict, all_params)
        except Exception as e:
            execution_model.import_errors.append(f"Error calling function '{method_value}': {e!s}")
            return

        call.result = results

        if result_value:
            execution_model.context.set_variable(result_value, results)
