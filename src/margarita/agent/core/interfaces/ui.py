from abc import ABC, abstractmethod

from margarita.agent.core.agents.models import ExecutionModel


class UI(ABC):
    """Abstract UI interface implemented by CLI writers and rich widgets.

    Provides methods for rendering output and updating progress in the terminal.
    """

    @abstractmethod
    async def render_ui(self, execution_model: ExecutionModel):
        """Render the UI for the agent execution.

        Args:
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
