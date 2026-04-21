from margarita.agent.entities.content_block import ContentBlock
from margarita.agent.entities.function import FunctionCall
from margarita.agent.entities.run import Run, RunError


def marks_dirty(func):
    """Decorator that sets `_is_dirty = True` on the instance before executing the wrapped method or property getter."""

    def wrapper(self, *args, **kwargs):
        self._is_dirty = True
        return func(self, *args, **kwargs)

    return wrapper


class Turn:
    """Represents a single LLM turn during execution.

    Contains the prompt, model response, and any metadata produced for the
    turn that may be persisted in the run history.
    """

    _is_dirty: bool
    _run: Run | None
    _function_calls: list[FunctionCall]
    _content_blocks: list[ContentBlock]
    _errors: list[RunError]

    def __init__(
        self,
        run: Run | None,
        function_calls: list[FunctionCall],
        content_blocks: list[ContentBlock],
    ):
        self._is_dirty = False
        self._run = run
        self._function_calls = function_calls
        self._content_blocks = content_blocks
        self._errors = []

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    def clear_dirty(self) -> None:
        self._is_dirty = False

    @property
    def run(self) -> Run | None:
        return self._run

    @run.setter
    def run(self, run: Run | None) -> None:
        self._run = run

    @property
    def errors(self) -> list[RunError]:
        return self._errors

    @property
    def function_calls(self) -> list[FunctionCall]:
        return self._function_calls

    @property
    def content_blocks(self) -> list[ContentBlock]:
        return self._content_blocks

    @marks_dirty
    def add_function_call(self, function_call: FunctionCall) -> None:
        self._function_calls.append(function_call)

    @marks_dirty
    def add_content_block(self, content_block: ContentBlock) -> None:
        self._content_blocks.append(content_block)

    @marks_dirty
    def add_error(self, error: RunError):
        self._errors.append(error)
