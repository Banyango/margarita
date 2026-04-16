import json
from pathlib import Path
from typing import Any

from margarita.agent.entities.context import Context


class Memory:
    def __init__(self, context: Context, save_path: Path | None = None):
        self._memory: dict[str, Any] = {}
        self.context = context
        self.save_path = save_path

    def set(self, name: str, value: Any) -> None:
        """Set a value in memory.

        Args:
            name (str): The name of the memory variable.
            value (Any): The value to store in memory.
        """
        self._memory[name] = value
        self.context.set_variable(name, value)
        self._persist()

    def _persist(self) -> None:
        if self.save_path is None:
            return
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.save_path.write_text(json.dumps(self.get_all(), indent=2, sort_keys=True) + "\n")

    def get_all(self) -> dict[str, Any]:
        """Get all memory values."""
        output = {}
        for key in self._memory.keys():
            output[key] = self.context.get_variable_value(key)
        return output

    def clear(self):
        """Clear all memory."""
        for key in list(self._memory.keys()):
            self.delete(key)

    def delete(self, name: str):
        if name in self._memory:
            del self._memory[name]

        self.context.delete(name)
        self._persist()

    def get_variable_value(self, key: str) -> Any:
        """Get the value of a memory variable by key.

        Args:
            key (str): The name of the memory variable to retrieve.
        """
        return self.context.get_variable_value(key)

    def get_items(self) -> dict[str, Any]:
        """Get all memory items as a dictionary."""
        return self._memory
