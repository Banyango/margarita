from abc import ABC, abstractmethod


class LoggerService(ABC):
    """Abstract logging service interface for writing runtime logs.

    Concrete implementations should provide methods for info/debug/error logging
    suitable for CLI and file outputs.
    """

    @abstractmethod
    def print(self, delta_content: str):
        """Print new content to the logger.

        Args:
            delta_content (str): The new content to print.
        """
