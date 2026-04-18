from abc import ABC, abstractmethod

from rich.panel import Panel
from rich.text import Text

from margarita.agent.entities.run import ToolCall


class ToolcallHandler(ABC):
    @abstractmethod
    def handles(self, tool_name: str) -> bool:
        """Check if the tool call is handled by this renderer

        Args:
            tool_name (str): the tool name
        """
        return tool_name == "view"

    @abstractmethod
    def render(self, tc: ToolCall) -> Text | Panel:
        """Render the tool call

        Args:
            tc (ToolCall): the tool call
        """
        pass
