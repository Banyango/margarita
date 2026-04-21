from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from margarita.agent.core.agents.models import (
    ExecutionModel,
    InputRequest,
    PermissionPrompt,
    Run,
    RunStatus,
)
from margarita.agent.core.agents.services.memory import MemoryService
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin
from margarita.agent.core.interfaces.prompt_integrity import PromptIntegrity
from margarita.agent.entities.context import Context
from margarita.agent.entities.turn import Turn

# Must stay in sync with _SUB_RUN_PALETTE in textual_app.py
_EXEC_COLOR_PALETTE = ["#00d7ff", "#ff5fff", "#ffd700", "#87ff00", "#ff8700", "#af87ff"]


class _MirroredTurnList(list):
    """A list that mirrors every append into a parent turns list.

    Used so child-model turns appear in the parent ExecutionModel immediately
    as they are created, giving the UI live visibility into sub-execution output
    without waiting for the child to finish.
    """

    def __init__(self, parent_turns: list[Turn]) -> None:
        super().__init__()
        self._parent = parent_turns

    def append(self, item: Turn) -> None:  # type: ignore[override]
        super().append(item)
        self._parent.append(item)


class _SubExecutionModel(ExecutionModel):
    """ExecutionModel variant for sub-executions.

    - Stamps is_sub_run and title on every new run immediately.
    - Routes input/permission requests through the parent model's locks so
      parallel sub-execs queue rather than race (no lost requests, no deadlock).
    """

    def __init__(self, exec_title: str, parent_model: ExecutionModel) -> None:
        super().__init__()
        self._exec_title = exec_title
        self._parent_model = parent_model
        self._color_hex = ""  # resolved on first start_run, once position in parent is known

    async def request_input(self, request: InputRequest) -> None:
        """Request input from the parent model. Blocks until parent model lock is free.

        Args:
            request: Input request.
        """
        if not request.source:
            request.source = self._exec_title
        request.color_hex = self._color_hex
        async with self._parent_model._input_lock:
            self._parent_model.pending_input = request
            await request.event.wait()
            self._parent_model.pending_input = None

    async def request_permission(self, prompt: PermissionPrompt) -> None:
        """Request permission from the parent model. Blocks until parent model lock is free.

        Args:
            prompt: Permission prompt.
        """
        if not prompt.source:
            prompt.source = self._exec_title
        prompt.color_hex = self._color_hex
        async with self._parent_model._permission_lock:
            self._parent_model.pending_permission = prompt
            await prompt.event.wait()
            self._parent_model.pending_permission = None

    def start_turn(self) -> Turn:
        """Start a new turn and resolve the sub-run color on the first turn.

        The color must be set before any input/permission request can be made
        (e.g. @effect input fires before @effect run), so it cannot wait until
        start_run.  At this point the mirrored turn has already been appended to
        the parent list, so counting parent turns gives the correct palette index.
        """
        turn = super().start_turn()
        if not self._color_hex and len(self.turns) == 1:
            idx = len(self._parent_model.turns) - 1
            self._color_hex = _EXEC_COLOR_PALETTE[idx % len(_EXEC_COLOR_PALETTE)]
        return turn

    def start_run(
        self, name: str, prompt: str, provider: str, status: RunStatus, start_time: datetime
    ) -> Run:
        """Start a new run and return it.

        Args:
            name: Name of the run
            prompt: Permission prompt.
            provider: Permission provider.
            status: Run status.
            start_time: Run start time.

        Returns:
            Run: The started run with sub-run metadata stamped.
        """
        run = super().start_run(
            name="SubRun", prompt=prompt, provider=provider, status=status, start_time=start_time
        )
        run.is_sub_run = True
        run.title = self._exec_title
        return run


class ExecPlugin(AgentPlugin):
    """Plugin that executes an isolated sub-.mgx file as a child operation.

    Handles @effect exec directives, resolving input variables from the parent
    context and copying declared output variables back after child execution.
    """

    def __init__(
        self,
        plugin_factory: Callable[[], list[AgentPlugin]],
        memory_service: MemoryService,
        prompt_integrity: PromptIntegrity | None = None,
        allow_unverified: bool = False,
    ):
        self.plugin_factory = plugin_factory
        self.memory_service = memory_service
        self.prompt_integrity = prompt_integrity
        self.allow_unverified = allow_unverified
        self.base_path: Path = Path.cwd()

    def set_base_path(self, path: Path) -> None:
        self.base_path = path

    def is_match(self, token: str) -> bool:
        return token == "exec"

    async def handle(self, params: str, execution_model: ExecutionModel) -> None:
        # Split on ` => ` to separate LHS (file + inputs) from RHS (output vars)
        if " => " in params:
            lhs, rhs = params.split(" => ", 1)
            output_vars = [v.strip() for v in rhs.split(",") if v.strip()]
        else:
            lhs = params
            output_vars = []

        tokens = lhs.split()
        if not tokens:
            raise ValueError("exec: missing file path")

        file_path_str = tokens[0]
        input_pairs = tokens[1:]

        # Resolve input variables from parent context
        resolved_inputs: dict[str, object] = {}
        for pair in input_pairs:
            if "=" in pair:
                key, val = pair.split("=", 1)
                resolved = execution_model.context.get_variable_value(val)
                resolved_inputs[key] = resolved if resolved is not None else val
            # Tokens without '=' are ignored (not a key=var assignment)

        # Resolve child file path
        child_path = (self.base_path / file_path_str).resolve(strict=False)
        if not child_path.exists():
            raise FileNotFoundError(f"exec: sub-mgx file not found: '{child_path}'")

        mgx_content = child_path.read_text()

        # Import here to avoid circular imports at module load time
        from margarita.agent.core.agents.operations.execute_agent_operation import (
            ExecuteAgentOperation,
        )

        exec_title = f"exec: {file_path_str}"

        child_model = _SubExecutionModel(exec_title, parent_model=execution_model)
        child_model.context = Context(resolved_inputs)
        # Mirror child turns into the parent list so the UI sees live updates
        # during execution rather than waiting for the child to finish.
        child_model.turns = _MirroredTurnList(execution_model.turns)

        child_op = ExecuteAgentOperation(
            plugins=self.plugin_factory(),
            execution_model=child_model,
            memory_service=self.memory_service,
            prompt_integrity=self.prompt_integrity,
            allow_unverified=self.allow_unverified,
        )
        await child_op.execute_async(mgx_content, base_path=child_path.parent)

        # Copy declared outputs to parent context
        for name in output_vars:
            value = child_model.context.get_variable_value(name)
            execution_model.context.set_variable(name, value)
