from textual.widgets import Static


class RunHeader(Static):
    """Clickable one-line summary for a RunWidget."""

    ALLOW_SELECT = False

    DEFAULT_CSS = """
    RunHeader {
        width: 1fr;
        height: auto;
    }
    """
