import json

from rich.console import Group
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from margarita.agent.app.ui.components.run_widget.tool_call_handlers.interfaces import (
    ToolcallHandler,
)
from margarita.agent.entities.run import ToolCall


class DefaultToolCallHandler(ToolcallHandler):
    def handles(self, tool_name: str) -> bool:
        return True

    def render(self, tc: ToolCall) -> Text | Panel:
        if tc.success is None:
            status_icon, status_style, border_style = "⌛", "yellow", "yellow dim"
        elif tc.success:
            status_icon, status_style, border_style = "✔", "green", "green dim"
        else:
            status_icon, status_style, border_style = "✗", "red", "red dim"

        tool_text = Text()
        tool_text.append(f"{status_icon} ", style=status_style)
        tool_text.append(tc.tool_name, style="bold")
        if tc.duration_ms is not None:
            tool_text.append(f"  {tc.duration_ms:.0f}ms", style="dim")

        tool_parts = [tool_text]

        if tc.arguments:
            try:
                args_str = json.dumps(tc.arguments, indent=2)
                tool_parts.append(Syntax(args_str, "json", theme="monokai", line_numbers=False))
            except (TypeError, ValueError):
                tool_parts.append(Text(str(tc.arguments), style="dim"))

        if tc.result:
            tool_parts.append(Text(tc.result, style="dim"))

        return Panel(Group(*tool_parts), border_style=border_style, expand=True, padding=(0, 1))
