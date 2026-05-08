from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Group
from rich.text import Text
from textual import on
from textual.containers import Vertical
from textual.events import Click
from textual.message import Message
from textual.widgets import Static

from margarita.agent.app.ui.components.run_widget.run_header import RunHeader
from margarita.agent.app.ui.components.run_widget.run_widget_content import RunWidgetContent
from margarita.agent.app.ui.components.run_widget.run_widget_header import RunWidgetHeader
from margarita.agent.app.ui.status_constants import NUM_SUB_COLORS

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from margarita.agent.app.config import AppConfig
    from margarita.agent.entities.run import Run


class RunWidget(Vertical):
    """A single execution turn: clickable header + collapsible content."""

    DEFAULT_CLASSES = "block"

    class CollapseChanged(Message):
        """Posted when the user explicitly collapses or expands a parent (non-sub) run."""

        def __init__(self, widget: RunWidget, expanded: bool) -> None:
            super().__init__()
            self.run_widget = widget
            self.expanded = expanded

    def __init__(self, index: int, app_config: AppConfig) -> None:
        super().__init__()
        self._index = index
        self._run: Run | None = None
        self._tool_call_cache: dict = {}
        self.app_config = app_config
        self._content: RunWidgetContent = RunWidgetContent()
        self._header: RunWidgetHeader | None = RunWidgetHeader(index=index)

    def compose(self) -> ComposeResult:
        yield RunHeader(id="run-header")
        yield Static(id="run-content")

    def on_mount(self) -> None:
        self._refresh_header()
        self._refresh_content()

    def sync(self, run: Run) -> None:
        """Called every poll tick with the latest data for this turn."""
        self._run = run
        self.set_class(run.is_sub_run, "-sub-run")
        self.set_class(run.is_expanded, "-expanded")

        if run.is_sub_run:
            color_idx = self._index % NUM_SUB_COLORS
            for i in range(NUM_SUB_COLORS):
                self.set_class(i == color_idx, f"-sub-color-{i}")

        self._refresh_header()
        self._refresh_content()

    @on(Click, "RunHeader")
    def _on_header_click(self, event: Click) -> None:
        event.stop()
        self._run.on_expanded()
        self.set_class(self._run.is_expanded, "-expanded")
        self._content_fp = None
        self._refresh_header()
        self._refresh_content()
        if not self._run.is_sub_run:
            self.post_message(self.CollapseChanged(self, self._run.is_expanded))

    def _refresh_header(self) -> None:
        if self._run is None:
            return

        self._header.status = self._run.status
        self._header.name = self._run.name
        self._header.duration_ms = self._run.duration_ms
        self._header.tokens = self._run.tokens.total_tokens
        self._header.model = self._run.model
        self._header.event_name = self._run.event_name.value if self._run.event_name else ""
        self._header.title = self._run.title
        self._header.is_sub_run = self._run.is_sub_run
        self._header.is_expanded = self._run.is_expanded

        if not self._header.is_dirty:
            return

        try:
            header = self.query_one("#run-header", RunHeader)
        except Exception:
            return

        header.update(self._header.render())
        self._header.clear_dirty()

    def _refresh_content(self) -> None:
        if self._run is None or not self._run.is_expanded:
            return

        if not self._content.should_render(run=self._run):
            return

        try:
            content = self.query_one("#run-content", Static)
        except Exception:
            return

        parts: list = []

        parts.extend(self._content.refresh_content(self._run, self.app_config))

        content.update(Group(*parts) if parts else Text(""))
