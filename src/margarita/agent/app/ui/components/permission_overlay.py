from typing import ClassVar

from rich.console import Group
from rich.syntax import Syntax
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static

from margarita.agent.core.agents.models import PermissionPrompt


class PermissionOverlay(Vertical):
    """Approve/deny overlay shown when the agent requests a permission.

    Posts PermissionOverlay.Resolved so the parent app can unblock the pending
    PermissionPrompt without coupling this widget to the execution model.
    """

    _KIND_LABELS: ClassVar = {
        "shell": "Shell command",
        "write": "File write",
        "read": "File read",
        "url": "URL access",
        "mcp": "MCP tool",
        "custom-tool": "Custom tool",
    }

    class Resolved(Message):
        def __init__(self, approved: bool) -> None:
            super().__init__()
            self.approved = approved

    def compose(self) -> ComposeResult:
        yield Static(id="perm-title")
        yield Static(id="perm-details")
        yield Static("  [bold green]a[/] Approve   [bold red]d[/] Deny", markup=True)

    def show(self, prompt: PermissionPrompt) -> None:
        self.display = True
        color = prompt.color_hex or None
        if color:
            self.styles.border_top = ("solid", color)
        else:
            # See note above: avoid CSS variable names that Textual's
            # Color.parse() can't resolve during tests.
            self.styles.border_top = ("solid", "yellow")
        label = self._KIND_LABELS.get(prompt.kind, prompt.kind)
        t = Text.from_markup(f"[bold yellow]⚠  Permission request:[/]  {label}")
        if prompt.source:
            t.append(f"  [{prompt.source}]", style=f"dim {color}" if color else "dim cyan")
        self.query_one("#perm-title", Static).update(t)
        diff = prompt.details.get("diff")
        detail_parts = [
            f"{k}: {v}"
            for k, v in prompt.details.items()
            if k not in ("kind", "diff") and v is not None
        ]
        renderables = []
        if detail_parts:
            renderables.append(Text("  " + "  ".join(detail_parts), style="dim"))
        if diff:
            renderables.append(Syntax(diff, "diff", theme="monokai", line_numbers=False))
        content = (
            Group(*renderables) if renderables else Text("  (no additional details)", style="dim")
        )
        self.query_one("#perm-details", Static).update(content)

    def hide(self) -> None:
        self.display = False
