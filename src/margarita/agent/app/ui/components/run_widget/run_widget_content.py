from __future__ import annotations

import re
from typing import TYPE_CHECKING

from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from margarita.agent.app.ui.components.run_widget.margarita_var_tool_call import (
    MargaritaVarToolCall,
)
from margarita.agent.entities.run import ContentBlock, ContentBlockType, Run, RunStatus, ToolCall

if TYPE_CHECKING:
    from margarita.agent.app.config import AppConfig
    from margarita.agent.entities.function import FunctionCall


class RunWidgetContent:
    def __init__(self):
        self.num_content_blocks = 0
        self.tool_calls = 0
        self.status = None
        self.last_text_len: int = 0
        self.completed_tool_calls: int = 0
        self._tool_call_cache: dict = {}

    def should_render(self, run: Run) -> bool:
        num_content_blocks = len(run.content_blocks)
        tool_calls = len(run.tool_calls)
        status = run.status
        last_text_len = len(run.content_blocks[-1].text) if run.content_blocks else 0
        completed_tool_calls = sum(1 for tc in run.tool_calls if tc.success is not None)

        return (num_content_blocks, tool_calls, status, last_text_len, completed_tool_calls) != (
            self.num_content_blocks,
            self.tool_calls,
            self.status,
            self.last_text_len,
            self.completed_tool_calls,
        )

    def refresh_content(self, run: Run, app_config: AppConfig):
        parts: list = []

        parts.extend(self.render_run(run, app_config))

        return parts

    def render_run(self, run: Run, app_config: AppConfig) -> list:
        parts = []

        if app_config.show_context and run.provider != "local":
            parts.append(Text("Prompt:", style="bold blue"))
            parts.append(Text(run.prompt, style="dim"))

        tool_call_map = {tc.tool_call_id: tc for tc in run.tool_calls}

        for block in run.content_blocks:
            if block.type == ContentBlockType.REASONING:
                continue
            elif block.type == ContentBlockType.RESPONSE:
                if not block.text:
                    continue
                parts.append(Text("Response:", style="bold blue"))
                try:
                    parts.append(Markdown(block.text))
                except Exception:
                    parts.append(Text(block.text))
            elif block.type == ContentBlockType.TOOL_CALL:
                tc = tool_call_map.get(block.ref)
                if tc:
                    parts.append(self._get_or_render_tool_call(tc))
            elif block.type == ContentBlockType.INPUT:
                parts.append(self._render_input(block))
            elif block.type == ContentBlockType.LOGGING:
                if not block.text:
                    continue
                parts.append(Text(f"[INFO] {block.text}", style="cyan dim"))
            elif block.type == ContentBlockType.QUESTION:
                parts.append(self._render_question(block))

        # Errors
        for err in run.errors:
            parts.append(
                Panel(
                    Text(err.message, style="red"),
                    title=f"Error{f' ({err.error_type})' if err.error_type else ''}",
                    border_style="red",
                    expand=True,
                )
            )

        # Usage summary (only when run is done)
        if run.status == RunStatus.COMPLETED and run.tokens.total_tokens > 0:
            usage = Table.grid(padding=(0, 2))
            usage.add_row(
                Text("Tokens:", style="dim"),
                Text(f"{run.tokens.input_tokens:,} in", style="dim"),
                Text(f"{run.tokens.output_tokens:,} out", style="dim"),
            )
            if run.request_count > 0:
                usage.add_row(
                    Text("Requests:", style="dim"),
                    Text(str(run.request_count), style="dim"),
                )
            parts.append(usage)

        # Code changes
        if run.code_changes:
            cc = run.code_changes
            changes_text = Text()
            changes_text.append(f"{len(cc.files_modified)} files", style="dim")
            changes_text.append(f"  +{cc.lines_added}", style="green")
            changes_text.append(f"  -{cc.lines_removed}", style="red")
            parts.append(changes_text)

        return parts

    def _get_or_render_tool_call(self, tc: ToolCall):
        if tc.success is not None:
            cached = self._tool_call_cache.get(tc.tool_call_id)
            if cached is not None:
                return cached
            rendered = (
                MargaritaVarToolCall.render(tc)
                if MargaritaVarToolCall.handles(tc.tool_name)
                else self._render_tool_call(tc)
            )
            self._tool_call_cache[tc.tool_call_id] = rendered
            return rendered
        if MargaritaVarToolCall.handles(tc.tool_name):
            return MargaritaVarToolCall.render(tc)
        return self._render_tool_call(tc)

    @staticmethod
    def _render_tool_call(tc: ToolCall) -> Panel:
        import json

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

    @staticmethod
    def _render_input(tc: ContentBlock) -> Panel:
        return Panel(Group(Markdown(tc.text)), border_style="dim", expand=True)

    @staticmethod
    def render_function_calls(function_calls: list[FunctionCall]) -> list:
        return [
            Panel(
                Group(
                    Text("❯  " + fc.method, style="bold cyan"),  # noqa: RUF001
                    Syntax(fc.params, "python", theme="monokai", line_numbers=False),
                    Text((fc.result or "")[0:150], style="dim"),
                ),
                title="fn",
                border_style="cyan dim",
                expand=True,
                padding=(0, 1),
            )
            for fc in function_calls
        ]

    @staticmethod
    def _render_question(tc: ContentBlock) -> Panel:
        # Convert literal "\\n" sequences into actual newlines so that
        # text containing escaped newlines displays correctly.
        text = tc.text.replace("\\n", "\n") if tc.text else ""

        # Markdown (CommonMark) doesn't treat a single newline as a line
        # break. Convert single newlines into 'two spaces + newline' so
        # Rich's Markdown will render them as visible line breaks while
        # preserving paragraph breaks (double newlines).
        # Accept optional CR before LF to handle Windows-style line endings
        text = re.sub(r"(?<!\n)\r?\n(?!\n)", "  \n", text)

        return Panel(Group(Markdown(f"""[Question]\nLi{text}""")), border_style="dim", expand=True)
