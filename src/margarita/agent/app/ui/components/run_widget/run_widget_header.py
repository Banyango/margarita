from __future__ import annotations

from rich.text import Text

from margarita.agent.app.ui.status_constants import (
    NUM_SUB_COLORS,
    STATUS_ICON,
    STATUS_STYLE,
    SUB_RUN_PALETTE,
)
from margarita.agent.entities.run import RunStatus


class RunWidgetHeader:
    """Header fingerprint container with per-field dirty tracking.

    Each attribute exposes a property that sets `_is_dirty` to True when the
    incoming value differs from the stored value. This allows the parent
    widget to efficiently detect when header values change.
    """

    def __init__(
        self,
        index: int = 0,
        status=None,
        name: str | None = None,
        duration_ms=None,
        total_tokens: int = 0,
        model=None,
        event_name=None,
        title=None,
        is_sub_run: bool = False,
        is_expanded: bool = False,
    ) -> None:
        self._name: str | None = name
        self._index = index
        self._status = status
        self._duration_ms = duration_ms
        self._total_tokens = total_tokens
        self._model = model
        self._event_name = event_name
        self._title = title
        self._is_sub_run = is_sub_run
        self._is_expanded = is_expanded
        self._is_dirty = False

    # helpers
    def clear_dirty(self) -> None:
        self._is_dirty = False

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    @property
    def status(self):
        return self._status

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value != self._name:
            self._name = value
            self._is_dirty = True

    @status.setter
    def status(self, value):
        if value != self._status:
            self._status = value
            self._is_dirty = True

    @property
    def duration_ms(self):
        return self._duration_ms

    @duration_ms.setter
    def duration_ms(self, value):
        if value != self._duration_ms:
            self._duration_ms = value
            self._is_dirty = True

    @property
    def total_tokens(self):
        return self._total_tokens

    @total_tokens.setter
    def total_tokens(self, value):
        if value != self._total_tokens:
            self._total_tokens = value
            self._is_dirty = True

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        if value != self._model:
            self._model = value
            self._is_dirty = True

    @property
    def event_name(self):
        return self._event_name

    @event_name.setter
    def event_name(self, value):
        if value != self._event_name:
            self._event_name = value
            self._is_dirty = True

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if value != self._title:
            self._title = value
            self._is_dirty = True

    @property
    def is_sub_run(self):
        return self._is_sub_run

    @is_sub_run.setter
    def is_sub_run(self, value: bool):
        if value != self._is_sub_run:
            self._is_sub_run = value
            self._is_dirty = True

    @property
    def is_expanded(self):
        return self._is_expanded

    @is_expanded.setter
    def is_expanded(self, value: bool):
        if value != self._is_expanded:
            self._is_expanded = value
            self._is_dirty = True

    def render(self) -> Text:
        """Render the header."""

        chevron = "▼" if self.is_expanded else "▶"
        status_icon = STATUS_ICON.get(self.status, "○")
        status_style = STATUS_STYLE.get(self.status, "dim")

        t = Text()
        t.append(f" {chevron} ", style="dim")

        if self.is_sub_run:
            color = SUB_RUN_PALETTE[self._index % NUM_SUB_COLORS]
            run_name = "Sub Run"
            if self.name:
                run_name = self.name
            t.append(run_name, style=f"bold {color}")
            if self.title:
                t.append(f"  {self.title}", style=f"dim {color}")
        else:
            run_name = f"Run {self._index + 1}"
            if self.name:
                run_name = self.name
            t.append(f"{run_name}", style="bold")
            if self.title:
                t.append(f"  {self.title}", style="dim cyan")

        if self.model:
            t.append(f"  {self.model}", style="dim")

        t.append(f"  {status_icon} {self.status.value}", style=status_style)

        if self.duration_ms is not None:
            t.append(f"  {self.duration_ms / 1000:.1f}s", style="dim")

        if self.total_tokens > 0 and not self.is_expanded:
            t.append(f"  {self.total_tokens:,} tok", style="dim")

        if self.event_name and not self.is_expanded:
            t.append(f"  {self.event_name}", style="dim")

        if not self.is_expanded and self.status not in (RunStatus.RUNNING, RunStatus.PENDING):
            t.append("  (expand)", style="italic dim")

        return t

    # comparison helpers so the object can be compared against the tuple
    def as_tuple(self):
        return (
            self._status,
            self._duration_ms,
            self._total_tokens,
            self._model,
            self._event_name,
            self._title,
            self._is_sub_run,
            self._is_expanded,
        )

    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.as_tuple() == other
        if isinstance(other, RunWidgetHeader):
            return self.as_tuple() == other.as_tuple()
        return NotImplemented

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"RunWidgetHeader({self.as_tuple()})"
