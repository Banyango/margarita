from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Input, Static


class InputOverlay(Vertical):
    """Prompt + text input shown when the execution model needs user input.

    Posts InputOverlay.Submitted on Enter so the parent app can resolve the
    pending InputRequest without coupling this widget to the execution model.
    """

    class Submitted(Message):
        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    def compose(self) -> ComposeResult:
        yield Static(id="input-prompt")
        yield Input(id="input-field", placeholder="Type your answer and press Enter…")

    def show(self, prompt: str, source: str = "", color_hex: str = "") -> None:
        self.display = True
        if color_hex:
            self.styles.border_top = ("solid", color_hex)
        else:
            # Use a concrete color name here instead of a CSS variable
            # ('$primary') because Color.parse() cannot resolve CSS
            # variables in this context (causes failures in tests).
            self.styles.border_top = ("solid", "cyan")
        # If there is no source and no color, keep the simple string
        # value for compatibility with tests/mocks that expect a plain
        # string. Otherwise, use a Rich Text object to include styling.
        if not source and not color_hex:
            prompt_display = f"❯  {prompt}"
            self.query_one("#input-prompt", Static).update(prompt_display)
        else:
            t = Text()
            if source:
                t.append(f"{source}", style=f"dim {color_hex}" if color_hex else "dim cyan")
                t.append("\n❯  ", style="bold")
            else:
                t.append("❯  ", style="bold")
            t.append(prompt)
            self.query_one("#input-prompt", Static).update(t)
        self.query_one("#input-field", Input).focus()

    def hide(self) -> None:
        self.display = False

    @on(Input.Submitted)
    def _on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.post_message(self.Submitted(event.value))
        self.query_one("#input-field", Input).clear()
