import contextlib
import sys
from pathlib import Path
from typing import ClassVar

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.events import Timer
from textual.widgets import Footer, Header, Input, Static

from margarita.agent.app.config import AppConfig, save_app_config
from margarita.agent.app.ui.components.app_header import AppHeader
from margarita.agent.app.ui.components.input_overlay import InputOverlay
from margarita.agent.app.ui.components.permission_overlay import PermissionOverlay
from margarita.agent.app.ui.components.run_widget import RunWidget
from margarita.agent.app.ui.components.status_line import StatusLine
from margarita.agent.app.ui.components.turn_widget import TurnWidget
from margarita.agent.core.agents.models import ExecutionModel


class Margarita(App):
    """Textual app for margarita execution output."""

    CSS_PATH = (
        Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "app/display/margarita.tcss"
        if getattr(sys, "frozen", False)
        else Path(__file__).parent / "margarita.tcss"
    )

    BINDINGS: ClassVar = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle_auto_scroll", "Auto-scroll"),
        Binding("p", "toggle_permissions", "Use/Ignore Permissions"),
        Binding("c", "toggle_context", "Show/Hide Context"),
    ]

    def __init__(self, execution_model: ExecutionModel, app_config: AppConfig) -> None:
        super().__init__()
        self.app_config = app_config
        self._poll_timer = Timer | None
        self._model = execution_model
        self._auto_scroll = True
        self.theme = app_config.theme
        self._turn_widgets: dict[int, TurnWidget] = {}
        self._header_fp: tuple | None = None
        self._displayed_input: object = None
        self._displayed_permission: object = None
        self.header = AppHeader()
        self._status_line = StatusLine()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="scroll"):
            yield Static(id="header-content")
            yield Vertical(id="turns-container")
            yield Static(id="status-line")
        yield PermissionOverlay(id="perm-overlay")
        yield InputOverlay(id="input-overlay")
        yield Footer()

    def on_mount(self) -> None:
        self._poll_timer = self.set_interval(0.016, self._poll)

    def watch_theme(self, theme: str) -> None:
        self.theme = theme
        self.app_config.theme = theme
        save_app_config(self.app_config)

    async def _poll(self) -> None:
        await self._sync_turns()

        header_content = self.query_one("#header-content", Static)
        self.header.sync(self._model, header_content)

        status_line = self.query_one("#status-line", Static)
        self._status_line.sync(self._model, status_line)

        self._sync_input()
        self._sync_permission()

        if self._status_line.all_done:
            self._auto_scroll = False

        if self._auto_scroll:
            self.query_one("#scroll", VerticalScroll).scroll_end(animate=False)

        if self._model.done:
            self._poll_timer.stop()

    async def _sync_turns(self) -> None:
        turns = self._model.turns
        container = self.query_one("#turns-container", Vertical)

        for i, turn in enumerate(turns):
            if i not in self._turn_widgets:
                widget = TurnWidget(i, self.app_config)
                self._turn_widgets[i] = widget
                await container.mount(widget)

            await self._turn_widgets[i].sync(turn)

    def _sync_input(self) -> None:
        pending = self._model.pending_input
        overlay = self.query_one("#input-overlay", InputOverlay)

        if pending is not None:
            if pending is not self._displayed_input:
                self._displayed_input = pending
                overlay.show(pending.prompt, source=pending.source, color_hex=pending.color_hex)
        elif overlay.display:
            self._displayed_input = None
            overlay.hide()

    def _sync_permission(self) -> None:
        pending = self._model.pending_permission
        overlay = self.query_one("#perm-overlay", PermissionOverlay)
        if pending is not None:
            if pending is not self._displayed_permission:
                self._displayed_permission = pending
                overlay.show(pending)
        elif overlay.display:
            self._displayed_permission = None
            overlay.hide()

    # -- Message handlers ----------------------------------------------------

    @on(RunWidget.CollapseChanged)
    def _on_run_collapse_changed(self, event: RunWidget.CollapseChanged) -> None:
        """When a parent run collapses/expands, hide/show all immediately-following sub-run TurnWidgets."""
        sender = event.run_widget
        sorted_indices = sorted(self._turn_widgets)
        found = False
        for i in sorted_indices:
            tw = self._turn_widgets[i]
            rw = tw._run_widget
            if rw is sender:
                found = True
                continue
            if found:
                if rw is not None and rw._run and rw._run.is_sub_run:
                    tw.display = event.expanded
                else:
                    break

    @on(PermissionOverlay.Resolved)
    def _on_permission_resolved(self, event: PermissionOverlay.Resolved) -> None:
        pending = self._model.pending_permission
        if pending is None:
            return
        pending.approved = event.approved
        pending.event.set()

    @on(InputOverlay.Submitted)
    def _on_input_submitted(self, event: InputOverlay.Submitted) -> None:
        pending = self._model.pending_input
        if pending is None:
            return
        pending.response = event.value
        pending.event.set()

    # -- Actions -------------------------------------------------------------

    def action_toggle_auto_scroll(self) -> None:
        self._auto_scroll = not self._auto_scroll
        self.notify(f"Auto-scroll {'on' if self._auto_scroll else 'off'}")

    def action_toggle_permissions(self) -> None:
        config = self.app_config
        config.ignore_permissions = not config.ignore_permissions
        save_app_config(config)
        self.notify(f"Permission requests {'off' if config.ignore_permissions else 'on'}")

    def action_toggle_context(self):
        config = self.app_config
        config.show_context = not config.show_context
        save_app_config(config)
        self.notify(f"Context {'on' if config.show_context else 'off'}")

    def on_mouse_scroll_up(self, _event) -> None:
        self._auto_scroll = False

    def on_mouse_scroll_down(self, _event) -> None:
        self._auto_scroll = False

    def on_key(self, event) -> None:
        if event.key in ("up", "down", "pageup", "pagedown", "home", "end"):
            self._auto_scroll = False

        perm_overlay = self.query_one("#perm-overlay", PermissionOverlay)
        if perm_overlay.display:
            if event.key == "a":
                perm_overlay.post_message(PermissionOverlay.Resolved(approved=True))
                event.stop()
                return
            elif event.key == "d":
                perm_overlay.post_message(PermissionOverlay.Resolved(approved=False))
                event.stop()
                return
        # Intercept Shift+Enter when input overlay is visible to insert a newline
        try:
            key = getattr(event, "key", None)
            shift = getattr(event, "shift", False)
        except Exception:
            return

        if key == "enter" and shift:
            overlay = self.query_one("#input-overlay", InputOverlay)
            if overlay.display:
                event.stop()
                inp = self.query_one("#input-field", Input)
                current = getattr(inp, "value", "") or ""
                # Try to obtain cursor position; fallback to appending at end
                pos = getattr(inp, "cursor_position", None)
                if pos is None:
                    try:
                        pos = inp._cursor_position  # private fallback
                    except Exception:
                        pos = len(current)
                # Insert newline at cursor position
                new_val = current[:pos] + "\n" + current[pos:]
                inp.value = new_val
                # Move cursor after inserted newline if supported
                try:
                    inp.cursor_position = pos + 1
                except Exception:
                    with contextlib.suppress(Exception):
                        inp._cursor_position = pos + 1
                inp.focus()
                return
