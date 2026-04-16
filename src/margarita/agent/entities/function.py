from dataclasses import dataclass


@dataclass
class FunctionCall:
    """Represents a call to a local Python function made during agent execution."""

    method: str
    params: str
    result: str | None = None
