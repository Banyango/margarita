from dataclasses import dataclass
from enum import Enum


class ContentBlockType(Enum):
    """Enumeration of content block types used in run outputs."""

    REASONING = "reasoning"
    RESPONSE = "response"
    FUNCTION_CALL = "function_call"
    TOOL_CALL = "tool_call"
    INPUT = "input"
    QUESTION = "question"
    LOGGING = "logging"
    AWAIT_ALL = "await_all"
    OTHER = "other"


@dataclass
class ContentBlock:
    """Represents a single block of content produced during a run.

    Attributes:
        type: The ContentBlockType of this block.
        text: The textual content of this block.
        ref: An optional reference string (e.g. tool name, function name) associated with this block.
    """

    """A single block of content generated during a run, with a type and optional reference."""
    type: ContentBlockType
    text: str = ""
    ref: str | None = None
