import json
from datetime import datetime

import pytest

from margarita.agent import ExecutionModel, RunStatus, Turn


def _create_execution_model() -> ExecutionModel:
    return ExecutionModel()


@pytest.mark.asyncio
async def test_start_should_set_header_when_called():
    # Arrange
    model = _create_execution_model()

    # Act
    model.start()

    # Assert
    assert model.header == ""


@pytest.mark.asyncio
async def test_start_turn_should_create_and_append_turn_when_called():
    # Arrange
    model = _create_execution_model()

    # Act
    turn = model.start_turn()

    # Assert
    assert isinstance(turn, Turn)
    assert turn.run is None
    assert turn.function_calls == []
    assert len(model.turns) == 1
    assert model.turns[0] is turn


@pytest.mark.asyncio
async def test_current_run_should_return_none_when_no_turns():
    # Arrange
    model = _create_execution_model()

    # Act
    result = model.current_run

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_current_run_should_return_run_when_turn_has_run():
    # Arrange
    model = _create_execution_model()
    model.start_turn()
    now = datetime.now()
    run = model.start_run(
        name="test",
        prompt="test prompt",
        provider="openai",
        status=RunStatus.RUNNING,
        start_time=now,
    )

    # Act
    result = model.current_run

    # Assert
    assert result is run


@pytest.mark.asyncio
async def test_start_run_should_create_run_on_current_turn_when_called():
    # Arrange
    model = _create_execution_model()
    model.metadata = {"key": "value"}
    model.start_turn()
    now = datetime.now()

    # Act
    run = model.start_run(
        name="test",
        prompt="hello",
        provider="anthropic",
        status=RunStatus.PENDING,
        start_time=now,
    )

    # Assert
    assert run.prompt == "hello"
    assert run.provider == "anthropic"
    assert run.status == RunStatus.PENDING
    assert run.start_time == now
    assert run.tool_calls == []
    assert run.metadata == {"key": "value"}
    assert model.turns[-1].run is run


@pytest.mark.asyncio
async def test_add_function_call_log_should_append_to_current_turn_when_called():
    # Arrange
    model = _create_execution_model()
    model.start_turn()
    params = {"arg1": "value1", "arg2": 42}

    # Act
    fc = model.add_function_call_log(method="do_something", params=params)

    # Assert
    assert fc.method == "do_something"
    assert fc.params == json.dumps(params)
    assert len(model.turns[-1].function_calls) == 1
    assert model.turns[-1].function_calls[0] is fc


@pytest.mark.asyncio
async def test_add_import_error_should_append_error_when_called():
    # Arrange
    model = _create_execution_model()

    # Act
    model.add_import_error("ModuleNotFoundError: No module named 'foo'")
    model.add_import_error("ImportError: cannot import name 'bar'")

    # Assert
    assert len(model.import_errors) == 2
    assert model.import_errors[0] == "ModuleNotFoundError: No module named 'foo'"
    assert model.import_errors[1] == "ImportError: cannot import name 'bar'"
