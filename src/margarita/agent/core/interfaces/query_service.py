from abc import ABC, abstractmethod

from margarita.agent.core.agents.models import ExecutionModel


class QueryService(ABC):
    """Abstract interface for a service that can execute LLM queries.

    Implementations should provide methods to run queries and stream results.
    """

    @abstractmethod
    async def execute_query(self, execution_model: ExecutionModel) -> str:
        """Execute the agent with the given context.

        Args:
            execution_model (ExecutionModel): The execution model for the current agent run.
        """

    @abstractmethod
    async def clear_session(self):
        """Clear any session or context data associated with the query service."""
