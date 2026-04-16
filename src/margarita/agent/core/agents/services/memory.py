import json
from abc import ABC, abstractmethod

from margarita.agent.entities.context import Context
from margarita.agent.entities.memory import Memory


class MemoryService(ABC):
    @staticmethod
    def clear_memory(memory: Memory):
        """Clear all memory."""
        memory.clear()

    @staticmethod
    def delete_memory_variable(name: str, memory: Memory):
        """Delete a specific memory variable."""
        memory.delete(name)

    def add_memory_variable(self, value_group: str | None, name: str, memory: Memory):
        """Add a memory variable.

        Args:
            value_group (str | None): The raw value string to parse and store. If None, will attempt to resolve from context using the same name.
            name (str): The name of the memory variable to set.
            memory (Memory): The memory object to set.
        """
        if name in memory.get_items():
            # Already loaded from disk — preserve the saved value and ignore any explicit default.
            return

        if value_group is None:
            # No explicit value provided; try to resolve from context using the same name
            value = memory.context.get_variable_value(name)
        else:
            value_str = value_group.strip()
            value = self._parse_value(value_str, memory)

        memory.set(name, value)

    def _parse_value(self, value_str: str, memory: Memory):
        try:
            return json.loads(value_str)
        except (json.JSONDecodeError, ValueError):
            pass

        resolved = memory.get_variable_value(value_str)
        if resolved is not None:
            return resolved

        return value_str

    @abstractmethod
    async def save_memory(self, memory: Memory):
        """Persist memory to storage."""
        pass

    @abstractmethod
    async def load_memory(self, context: Context) -> Memory:
        """Load memory from storage."""
        pass
