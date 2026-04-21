from typing import Any

from rich.console import Group
from rich.rule import Rule
from rich.text import Text
from textual.widgets import Static

from margarita.agent.core.agents.models import ExecutionModel

LOGO = Text("┳┳┓          •   \n┃┃┃┏┓┏┓┏┓┏┓┏┓┓╋┏┓\n┛ ┗┗┻┛ ┗┫┗┻┛ ┗┗┗┻\n        ┛")


class AppHeader:
    def __init__(self):
        self.model = None
        self._import_errors = []
        self._warnings = []
        self._header = None
        self._metadata = None
        self._memory = None
        self._is_dirty = False

    @property
    def import_errors(self):
        return self._import_errors

    @property
    def warnings(self):
        return self._warnings

    @property
    def header(self):
        return self._header

    @property
    def metadata(self):
        return self._metadata

    @property
    def memory(self):
        return self._memory

    @import_errors.setter
    def import_errors(self, value):
        self._is_dirty = True
        self._import_errors = value

    @warnings.setter
    def warnings(self, value):
        self._is_dirty = True
        self._warnings = value

    @header.setter
    def header(self, value):
        self._is_dirty = True
        self._header = value

    @metadata.setter
    def metadata(self, value):
        self._is_dirty = True
        self._metadata = value

    @memory.setter
    def memory(self, value):
        self._is_dirty = True
        self._memory = value

    def sync(self, model: ExecutionModel, content: Static) -> None:
        """Update the header content based on the execution model."""
        self.model = model

        self.import_errors = model.import_errors
        self.warnings = model.warnings
        self.header = model.header
        self.metadata = model.metadata
        self.memory = model.memory

        if not self._is_dirty:
            return

        content.update(Group(*self.render(model)))

    def render(self, model: ExecutionModel | None = None) -> list[Any]:
        if model is not None:
            self.model = model

        renderables: list[Any] = [LOGO]

        if not self.model:
            return renderables

        if self.model.import_errors:
            renderables.append(Rule("Import Errors", style="red"))
            for err in self.model.import_errors:
                renderables.append(Text(str(err), style="red"))
            renderables.append(Rule(style="red"))
            renderables.append(Text())

        if self.model.warnings:
            renderables.append(Rule("Warnings", style="yellow"))
            for warning in self.model.warnings:
                renderables.append(Text(str(warning), style="yellow"))
            renderables.append(Rule(style="yellow"))
            renderables.append(Text())

        if self.model.header:
            renderables.append(Text(self.model.header, style="bold cyan"))
            renderables.append(Text())

        if self.model.metadata:
            renderables.append(Rule("Metadata", style="dim cyan"))
            for key, value in self.model.metadata.items():
                renderables.append(Text(f"{key}: {value}", style="dim"))
            renderables.append(Rule(style="dim cyan"))
            renderables.append(Text())

        if self.model.memory and self.model.memory.get_items():
            renderables.append(Rule("Memory", style="dim magenta"))
            for key, value in self.model.memory.get_items().items():
                renderables.append(Text(f"{key}: {value}", style="dim"))
            renderables.append(Rule(style="dim magenta"))
            renderables.append(Text())

        return renderables
