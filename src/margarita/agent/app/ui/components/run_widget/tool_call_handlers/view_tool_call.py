from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text

from margarita.agent.app.ui.components.run_widget.tool_call_handlers.interfaces import (
    ToolcallHandler,
)

if TYPE_CHECKING:
    from rich.panel import Panel

    from margarita.agent.entities.run import ToolCall

_MAX_VALUE_LEN = 80


class MargaritaViewToolCall(ToolcallHandler):
    def handles(self, tool_name: str) -> bool:
        """Check if the tool call is handled by this renderer

        Args:
            tool_name (str): the tool name
        """
        return tool_name == "view"

    def render(self, tc: ToolCall) -> Text | Panel:
        """Render the tool call

        Args:
            tc (ToolCall): the tool call
        """
        if tc.success is None:
            return Text(f"~ Reading file {tc.arguments['path']}", style="dim")
        if tc.success:
            return Text(f"~ Reading file {tc.arguments['path']}", style="spring_green1")

        return Text(f"x Failed Reading file {tc.arguments['path']}", style="red")
