from datetime import datetime
from pathlib import Path

from wireup import injectable

from margarita.agent.core.interfaces.logger import LoggerService


@injectable(as_type=LoggerService)
class FileLogger(LoggerService):
    def __init__(self):
        log_dir = Path.home() / ".margarita"
        log_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = log_dir / "margarita.log"

        # delete the log file if it already exists to start fresh on each run
        if self._log_path.exists():
            self._log_path.unlink()

    def print(self, delta_content: str):
        if not delta_content:
            return
        timestamp = datetime.now().isoformat(timespec="seconds")
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {delta_content}\n")
