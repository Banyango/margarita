from __future__ import annotations

import json
from typing import TYPE_CHECKING

from rich.text import Text

from margarita.agent.app.ui.components.run_widget.tool_call_handlers.interfaces import (
    ToolcallHandler,
)

if TYPE_CHECKING:
    from rich.panel import Panel

    from margarita.agent.entities.run import ToolCall

_STATE_VARIABLE_TOOLS = ("get_variable", "set_variable")
_MAX_VALUE_LEN = 80


def _join_truncated(parts: list[str], max_len: int = _MAX_VALUE_LEN) -> str:
    result = ""
    sep = "  |  "
    for _, part in enumerate(parts):
        candidate = (result + sep + part) if result else part
        if len(candidate) > max_len:
            truncated = part[: max(0, max_len - len(result) - len(sep) - 1)] + "…"
            result = (result + sep + truncated) if result else truncated
            break
        result = candidate
    return result


class MargaritaVarToolCall(ToolcallHandler):
    def handles(self, tool_name: str) -> bool:
        """Check if the tool call is handled by this renderer

        Args:
            tool_name (str): the tool name
        """
        return tool_name in _STATE_VARIABLE_TOOLS

    @staticmethod
    def _get_result(var_name: str, result: str) -> str:
        value_str = ""
        try:
            result_dict = json.loads(result)

            value = result_dict.get(var_name)

            if isinstance(value, dict):
                parts = [
                    f"{k}: {json.dumps(v) if isinstance(v, str) else v}" for k, v in value.items()
                ]
                value_str = _join_truncated(parts, max_len=80)
            elif value is not None:
                value_str = str(value)[:80]

        except (json.JSONDecodeError, AttributeError, TypeError):
            value_str = str(result)[:80]

        return value_str

    @staticmethod
    def _render_set_tool_call(tool_call: ToolCall) -> Text:
        text = Text()

        var_name = tool_call.arguments.get("name", "")
        value_str = str(tool_call.arguments.get("value", ""))[:80]

        if tool_call.success is None:
            text.append(f"↳ setting {var_name} = {value_str}", style="dim")
        elif tool_call.success:
            text.append(f"↳ set {var_name}", style="green")
            if value_str:
                text.append(" = ", style="green")
                text.append(value_str, style="green")
        else:
            text.append(f"X {var_name}", style="red dim")
            if value_str:
                text.append(f" = {value_str}", style="red dim")

        return text

    @staticmethod
    def _render_get_tool_call(tool_call: ToolCall) -> Text:
        text = Text()

        var_name = tool_call.arguments.get("variable", "")
        value_str = str(tool_call.arguments.get("value", ""))[:80]

        if tool_call.success is None:
            text.append(f"↓ getting {var_name}", style="dim")
        elif tool_call.success:
            text.append(f"↓ {var_name}", style="green")
            if tool_call.result:
                value_str = MargaritaVarToolCall._get_result(var_name, tool_call.result)
                if value_str:
                    text.append(f" : {value_str}", style="green")
        else:
            text.append(f"X {var_name}", style="red dim")

        return text

    def render(self, tc: ToolCall) -> Text | Panel:
        """Render the tool call

        Args:
            tc (ToolCall): the tool call
        """
        is_set = tc.tool_name == "set_variable"
        return (
            MargaritaVarToolCall._render_set_tool_call(tc)
            if is_set
            else MargaritaVarToolCall._render_get_tool_call(tc)
        )
