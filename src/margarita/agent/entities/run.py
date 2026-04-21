from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from margarita.agent.entities.content_block import ContentBlock, ContentBlockType


class RunStatus(Enum):
    """Lifecycle states for an agent Run."""

    PENDING = "starting"
    RUNNING = "running"
    IDLE = "idle"
    ERROR = "error"
    COMPLETED = "completed"


class ShutdownReason(Enum):
    """Reasons why a run may have been shut down."""

    ROUTINE = "routine"
    ERROR = "error"
    TIMEOUT = "timeout"
    ABORTED = "aborted"


@dataclass
class TokenUsage:
    """Token accounting for a run: input/output and cache-related tokens."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def accumulate(self, other: "TokenUsage"):
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_read_tokens += other.cache_read_tokens
        self.cache_write_tokens += other.cache_write_tokens


@dataclass
class ModelUsage:
    """Per-model usage and cost breakdown for a run."""

    model: str
    request_count: int = 0
    cost: float = 0.0
    tokens: TokenUsage = field(default_factory=TokenUsage)


class RunEventEnum(Enum):
    """Enumeration of significant events during a run that may be logged or emitted."""

    THINKING = "thinking"
    RUNNING = "running"
    REASONING = "reasoning"
    RESPONSE = "responding"
    FETCHING = "fetching"


@dataclass
class ToolCall:
    """Record of an individual tool invocation during a run."""

    tool_name: str
    tool_call_id: str
    arguments: Any = None
    result: str | None = None
    success: bool | None = None
    duration_ms: float | None = None
    parent_tool_call_id: str | None = None


@dataclass
class CodeChanges:
    """Summary of code modifications produced or applied by a run."""

    files_modified: list[str] = field(default_factory=list)
    lines_added: int = 0
    lines_removed: int = 0


class StopError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


@dataclass
class RunError:
    """Structured error information captured during a run."""

    message: str
    code: str | None = None
    stack: str | None = None
    error_type: str | None = None


@dataclass
class RunContext:
    """Execution environment context for a run (cwd, git metadata, repository info)."""

    cwd: str | None = None
    git_root: str | None = None
    branch: str | None = None
    repository_owner: str | None = None
    repository_name: str | None = None


@dataclass
class Run:
    """Comprehensive record of an agent Run, including lifecycle, usage, content, and results."""

    # Identity
    name: str | None = None
    session_id: str | None = None
    turn_id: str | None = None

    # Lifecycle
    status: RunStatus = RunStatus.PENDING
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_ms: float | None = None
    shutdown_reason: ShutdownReason | None = None

    # Model
    model: str | None = None
    provider: str | None = None

    # Usage (aggregated across all API calls in this run)
    tokens: TokenUsage = field(default_factory=TokenUsage)
    total_cost: float = 0.0
    request_count: int = 0
    model_usage: dict[str, ModelUsage] = field(default_factory=dict)

    # Content
    prompt: str | None = None
    responses: list[str] | None = None
    reasoning: list[str] | None = None
    content_blocks: list[ContentBlock] = field(default_factory=list)

    # Tool execution
    tool_calls: list[ToolCall] = field(default_factory=list)

    # Code impact
    code_changes: CodeChanges | None = None

    # Environment
    context: RunContext = field(default_factory=RunContext)

    # Extensible metadata (provider-specific data, telemetry, etc.)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Result of the run
    result: str | None = None

    # Display label (e.g. "exec: helpers/summarize.mgx" for sub-executions)
    title: str = ""

    # True when this run belongs to a sub-execution (@effect exec)
    is_sub_run: bool = False
    is_expanded: bool = True
    is_user_toggled: bool = False

    # DEBUG
    event_name: RunEventEnum | None = None

    def on_expanded(self) -> None:
        self.is_user_toggled = True
        self.is_expanded = not self.is_expanded

    def on_complete(self):
        self.is_expanded = False

    def add_log(self, param: str):
        """
        Add a log entry to the run's content blocks with the given text.

        Args:
            param (str): The log message to add as a content block.
        """
        self.content_blocks.append(ContentBlock(type=ContentBlockType.LOGGING, text=param))
