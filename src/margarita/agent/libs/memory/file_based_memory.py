import json
from pathlib import Path

from wireup import injectable

from margarita.agent.core.agents.services.memory import MemoryService
from margarita.agent.entities.context import Context
from margarita.agent.entities.memory import Memory


@injectable(as_type=MemoryService)
class FileBasedMemoryService(MemoryService):
    async def save_memory(self, memory: Memory):
        memory._persist()

    async def load_memory(self, context: Context):
        memory_path = Path.cwd() / "memory.json"
        memory = Memory(context, save_path=memory_path)

        if memory_path.is_file():
            try:
                data = json.loads(memory_path.read_text())
                memory.save_path = None
                for key, value in data.items():
                    memory.set(key, value)
                memory.save_path = memory_path
            except (json.JSONDecodeError, ValueError):
                pass

        return memory
