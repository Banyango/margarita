from margarita.agent.entities.run import RunStatus

# ── Status mappings ──────────────────────────────────────────────────────────

STATUS_STYLE: dict[RunStatus, str] = {
    RunStatus.PENDING: "dim",
    RunStatus.RUNNING: "bold yellow",
    RunStatus.IDLE: "bold cyan",
    RunStatus.COMPLETED: "bold green",
    RunStatus.ERROR: "bold red",
}

STATUS_ICON: dict[RunStatus, str] = {
    RunStatus.PENDING: "○",
    RunStatus.RUNNING: "◉",
    RunStatus.IDLE: "◎",
    RunStatus.COMPLETED: "●",
    RunStatus.ERROR: "✗",
}

SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

SUB_RUN_PALETTE = ["#00d7ff", "#ff5fff", "#ffd700", "#87ff00", "#ff8700", "#af87ff"]
NUM_SUB_COLORS = len(SUB_RUN_PALETTE)
