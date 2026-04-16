import io

from rich.console import Console, Group

from margarita.agent import ContentBlock, ContentBlockType, FunctionCall, Run, RunStatus, TokenUsage
from margarita.agent.app.config import AppConfig
from margarita.agent.app.ui.components.run_widget.run_widget_content import RunWidgetContent


def _create_writer() -> RunWidgetContent:
    return RunWidgetContent()


def _render_parts_to_str(parts: list) -> str:
    """Helper to render a list of Rich renderables to string."""
    console = Console(file=io.StringIO(), highlight=False)
    console.print(Group(*parts))
    return console.file.getvalue()


def test_render_run_should_include_response_content():
    # Arrange
    writer = _create_writer()
    run = Run(
        status=RunStatus.COMPLETED,
        provider="local",
        tool_calls=[],
        content_blocks=[ContentBlock(type=ContentBlockType.RESPONSE, text="Hello from the model")],
    )

    # Act
    parts = writer.render_run(run, AppConfig())

    # Assert
    output = _render_parts_to_str(parts)
    assert "Hello from the model" in output


def test_render_run_should_skip_empty_response_blocks():
    # Arrange
    writer = _create_writer()
    run = Run(
        status=RunStatus.COMPLETED,
        provider="local",
        tool_calls=[],
        content_blocks=[
            ContentBlock(type=ContentBlockType.RESPONSE, text=""),
            ContentBlock(type=ContentBlockType.RESPONSE, text="Actual content"),
        ],
    )

    # Act
    parts = writer.render_run(run, AppConfig())

    # Assert
    output = _render_parts_to_str(parts)
    assert "Actual content" in output


def test_render_run_should_include_token_usage_when_completed():
    # Arrange
    writer = _create_writer()
    run = Run(
        status=RunStatus.COMPLETED,
        provider="local",
        tool_calls=[],
        tokens=TokenUsage(input_tokens=100, output_tokens=50),
    )

    # Act
    parts = writer.render_run(run, AppConfig())

    # Assert
    output = _render_parts_to_str(parts)
    assert "100" in output
    assert "50" in output


def test_render_run_should_skip_reasoning_blocks():
    # Arrange
    writer = _create_writer()
    run = Run(
        status=RunStatus.COMPLETED,
        provider="local",
        tool_calls=[],
        content_blocks=[
            ContentBlock(type=ContentBlockType.REASONING, text="Internal reasoning"),
            ContentBlock(type=ContentBlockType.RESPONSE, text="Public response"),
        ],
    )

    # Act
    parts = writer.render_run(run, AppConfig())

    # Assert
    output = _render_parts_to_str(parts)
    assert "Internal reasoning" not in output
    assert "Public response" in output


# --- render_function_calls ---


def test_render_run_should_include_logging_blocks():
    # Arrange
    writer = _create_writer()
    run = Run(
        status=RunStatus.COMPLETED,
        provider="local",
        tool_calls=[],
        content_blocks=[ContentBlock(type=ContentBlockType.LOGGING, text="Log message")],
    )

    # Act
    parts = writer.render_run(run, AppConfig())

    # Assert
    output = _render_parts_to_str(parts)
    assert "Log message" in output


def test_render_function_calls_should_include_method_name():
    # Arrange
    writer = _create_writer()
    function_calls = [FunctionCall(method="my_func", params='{"x": 1}', result="42")]

    # Act
    parts = writer.render_function_calls(function_calls)

    # Assert
    output = _render_parts_to_str(parts)
    assert "my_func" in output


def test_render_function_calls_should_include_params():
    # Arrange
    writer = _create_writer()
    function_calls = [FunctionCall(method="my_func", params='{"x": 1}', result="42")]

    # Act
    parts = writer.render_function_calls(function_calls)

    # Assert
    output = _render_parts_to_str(parts)
    assert '"x": 1' in output


def test_render_function_calls_should_include_result():
    # Arrange
    writer = _create_writer()
    function_calls = [FunctionCall(method="my_func", params='{"x": 1}', result="Result value")]

    # Act
    parts = writer.render_function_calls(function_calls)

    # Assert
    output = _render_parts_to_str(parts)
    assert "Result value" in output


def test_render_function_calls_should_handle_empty_list():
    # Arrange
    writer = _create_writer()
    function_calls = []

    # Act
    parts = writer.render_function_calls(function_calls)

    # Assert
    assert parts == []


def test_render_function_calls_should_handle_multiple_calls():
    # Arrange
    writer = _create_writer()
    function_calls = [
        FunctionCall(method="func1", params='{"a": 1}', result="result1"),
        FunctionCall(method="func2", params='{"b": 2}', result="result2"),
    ]

    # Act
    parts = writer.render_function_calls(function_calls)

    # Assert
    output = _render_parts_to_str(parts)
    assert "func1" in output
    assert "func2" in output
    assert "result1" in output
    assert "result2" in output
