import re
from time import monotonic

from rich.text import Text
from textual.widgets import Static

from margarita.agent.app.ui.status_constants import SPINNER_FRAMES
from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.entities.content_block import ContentBlockType
from margarita.agent.entities.run import RunStatus


class StatusLine:
    def __init__(self):
        self._model: ExecutionModel | None = None

    def sync(self, model: ExecutionModel, component: Static):
        self._model = model

        if model is None:
            component.update(Text())
            return

        has_runs = model.turns and any(t.run for t in model.turns)
        if not has_runs:
            component.update(Text())
            return

        all_done = all(
            t.run and t.run.status in (RunStatus.COMPLETED, RunStatus.ERROR)
            for t in model.turns
            if t.run
        )

        if all_done:
            t = Text()
            t.append("● ", style="bold green")
            t.append("All turns completed  ", style="dim")
            t.append("q", style="bold")
            t.append(" to quit", style="dim")
            component.update(t)
            return

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

        component.update(t)

    @property
    def all_done(self) -> bool:
        model = self._model
        if model is None:
            return False
        return bool(
            model.turns
            and any(t.run for t in model.turns)
            and all(
                t.run and t.run.status in (RunStatus.COMPLETED, RunStatus.ERROR)
                for t in model.turns
                if t.run
            )
        )
