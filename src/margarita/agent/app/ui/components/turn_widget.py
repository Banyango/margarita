from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.containers import Vertical
from textual.widgets import Static

from margarita.agent.app.ui.components.run_widget import RunWidget
from margarita.agent.app.ui.components.run_widget.run_widget_content import RunWidgetContent

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from margarita.agent import Turn
    from margarita.agent.app.config import AppConfig


class TurnWidget(Vertical):
    """Renders a single turn: turn-level content blocks followed by its RunWidget."""

    def __init__(self, index: int, app_config: AppConfig) -> None:
        super().__init__()
        self._index = index
        self._turn: Turn | None = None
        self._run_widget: RunWidget | None = None
        self._content_widget: Static | None = None
        self._block_count: int = 0
        self.app_config = app_config

    def compose(self) -> ComposeResult:
        yield from ()

    async def sync(self, turn: Turn) -> None:
        """Called every poll tick with the latest turn data."""
        self._turn = turn

        # Mount content widget before RunWidget on first block arrival
        if turn.content_blocks and self._content_widget is None:
            self._content_widget = Static()
            before = self._run_widget if self._run_widget is not None else None
            await self.mount(self._content_widget, before=before)

        # Re-render content when block count changes
        if self._content_widget is not None:
            num_blocks = len(turn.content_blocks)
            if num_blocks != self._block_count:
                self._block_count = num_blocks
                self._refresh_content()

        # Mount RunWidget on first run
        if turn.run is not None and self._run_widget is None:
            self._run_widget = RunWidget(self._index, self.app_config)
            await self.mount(self._run_widget)
            # Re-assert content after Textual's layout pass
            self._refresh_content()

        if self._run_widget is not None and turn.run is not None:
            self._run_widget.sync(turn.run)

    def _refresh_content(self) -> None:
        if self._turn is None or self._content_widget is None:
            return
        parts = RunWidgetContent.render_content_blocks(self._turn.content_blocks)
        for err in self._turn.errors:
            parts.append(
                Panel(
                    Text(err.message, style="red"),
                    title=f"Error{f' ({err.error_type})' if err.error_type else ''}",
                    border_style="red",
                    expand=True,
                )
            )
        self._content_widget.update(Group(*parts) if parts else Text(""))
