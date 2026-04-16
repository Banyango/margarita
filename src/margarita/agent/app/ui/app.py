import re
import sys
from pathlib import Path
from time import monotonic

from rich.console import Group
from rich.text import Text
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
from margarita.agent.app.ui.status_constants import SPINNER_FRAMES
from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.entities.run import ContentBlockType, RunStatus


class Margarita(App):
    """Textual app for margarita execution output."""

    CSS_PATH = (
        Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "app/display/margarita.tcss"
        if getattr(sys, "frozen", False)
        else Path(__file__).parent / "margarita.tcss"
    )

    BINDINGS = [
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
        self._run_widgets: dict[int, RunWidget] = {}
        self._header_fp: tuple | None = None
        self._displayed_input: object = None
        self._displayed_permission: object = None
        self.header = AppHeader()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="scroll"):
            yield Static(id="header-content")
            yield Vertical(id="runs-container")
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
        await self._sync_runs()

        self._sync_header()
        self._sync_status()

        self._sync_input()
        self._sync_permission()

        if self._auto_scroll:
            self.query_one("#scroll", VerticalScroll).scroll_end(animate=False)

        if self._model.done:
            self._poll_timer.stop()

    def _sync_header(self) -> None:
        model = self._model
        memory_len = len(model.memory.get_items()) if model.memory else 0
        fp = (
            len(model.import_errors),
            len(model.warnings),
            model.header,
            len(model.metadata),
            memory_len,
        )
        if fp == self._header_fp:
            return
        self._header_fp = fp

        renderables = self.header.render(model)
        self.query_one("#header-content", Static).update(Group(*renderables))

    async def _sync_runs(self) -> None:
        turns = self._model.turns_with_runs
        container = self.query_one("#runs-container", Vertical)

        for i, turn in enumerate(turns):
            if turn.run is None:
                continue

            if i not in self._run_widgets:
                widget = RunWidget(i, self.app_config)
                self._run_widgets[i] = widget
                await container.mount(widget)

            self._run_widgets[i].sync(turn.run)

    def _sync_status(self) -> None:
        model = self._model
        has_runs = model.turns and any(t.run for t in model.turns)
        if not has_runs:
            self.query_one("#status-line", Static).update("")
            return

        all_done = all(
            t.run and t.run.status in (RunStatus.COMPLETED, RunStatus.ERROR)
            for t in model.turns
            if t.run
        )
        if all_done:
            self._auto_scroll = False

            t = Text()

            t.append("● ", style="bold green")
            t.append("All turns completed  ", style="dim")
            t.append("q", style="bold")
            t.append(" to quit", style="dim")

            self.query_one("#status-line", Static).update(t)
        else:
            frame = SPINNER_FRAMES[int(monotonic() * 10) % len(SPINNER_FRAMES)]

            t = Text()

            t.append(f"{frame} ", style="green")
            t.append("Executing…", style="dim")

            run = model.current_run
            if run is not None:
                reasoning_blocks = [
                    b for b in run.content_blocks if b.type == ContentBlockType.REASONING and b.text
                ]
                if reasoning_blocks:
                    latest = reasoning_blocks[-1].text
                    condensed = re.findall(r"\*\*(.+?)\*\*", latest)

                    snippet = condensed[-1] if condensed else latest
                    snippet = snippet.replace("\n", " ").strip()

                    if len(snippet) > 80:
                        snippet = snippet[:77] + "…"
                    t.append(f"  {snippet}", style="dim italic")

            self.query_one("#status-line", Static).update(t)

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
        """When a parent run collapses, collapse all immediately-following sub-runs."""
        if event.expanded:
            return
        sender = event.run_widget
        widgets = [self._run_widgets[i] for i in sorted(self._run_widgets)]
        found = False
        for w in widgets:
            if w is sender:
                found = True
                continue
            if found:
                if w._run and w._run.is_sub_run:
                    w._run.is_expanded = False
                    w.set_class(False, "-expanded")
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

    def on_mouse_scroll_up(self, event) -> None:
        self._auto_scroll = False

    def on_mouse_scroll_down(self, event) -> None:
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
                    try:
                        inp._cursor_position = pos + 1
                    except Exception:
                        pass
                inp.focus()
                return
