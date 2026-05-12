from margarita.agent import ExecutionModel, Run, RunStatus, TokenUsage
from margarita.agent.app.cli.writers.writer import CliWriter
from margarita.agent.app.config import AppConfig


def _create_writer() -> CliWriter:
    return CliWriter(app_config=AppConfig(show_context=False))


def _create_run(status: RunStatus = RunStatus.COMPLETED) -> Run:
    return Run(
        status=status,
        model="gpt-4o",
        duration_ms=1200.0,
        tokens=TokenUsage(input_tokens=100, output_tokens=50),
        tool_calls=[],
    )


def _create_execution_model_with_turns(
    count: int, status: RunStatus = RunStatus.COMPLETED
) -> ExecutionModel:
    model = ExecutionModel()
    model.start()
    for _ in range(count):
        model.start_turn()
        run = _create_run(status=status)
        model.turns[-1].run = run
    return model


# --- _build_status ---


# --- render_run ---
