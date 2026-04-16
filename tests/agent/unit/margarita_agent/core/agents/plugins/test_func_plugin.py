from datetime import datetime

import pytest

from margarita.agent import ExecutionModel, RunStatus
from margarita.agent.core.agents.plugins.func import FuncPlugin


def _create_execution_model():
    model = ExecutionModel()
    model.start_turn()
    return model


def test_func_should_match_when_token_is_func():
    # Arrange
    plugin = FuncPlugin()

    # Act
    matched = plugin.is_match("func")
    not_matched = plugin.is_match("other")

    # Assert
    assert matched is True
    assert not_matched is False


@pytest.mark.asyncio
async def test_func_should_run_function_and_store_result_when_params_provided():
    # Arrange
    execution_model = _create_execution_model()
    execution_model.context.set_variable("x", 2)
    execution_model.context.set_variable("y", 3)
    exec("def add(x, y):\n    return x + y", execution_model.globals_dict)
    plugin = FuncPlugin()
    params = "add(x,y) => result"

    # Act
    await plugin.handle(params, execution_model=execution_model)

    # Assert
    assert execution_model.context.get_variable_value("result") == 5
    assert len(execution_model.turns[-1].function_calls) == 1
    assert execution_model.turns[-1].function_calls[0].result == 5


@pytest.mark.asyncio
async def test_handle_should_run_func_when_valid():
    # Arrange
    plugin = FuncPlugin()
    assert plugin.is_match("func")

    execution_model = ExecutionModel()
    execution_model.start_turn()
    execution_model.start_run(
        prompt="p",
        provider="prov",
        status=RunStatus.PENDING,
        start_time=datetime.now(),
    )

    # Set variables that will be used as function arguments
    execution_model.context.set_variable("a", 2)
    execution_model.context.set_variable("b", 3)

    # Provide a function in the globals that will be invoked by the plugin
    exec("def add(a, b):\n    return a + b", execution_model.globals_dict)

    params = "add(a, b) => sum_result"

    # Act
    await plugin.handle(params, execution_model=execution_model)

    # Assert
    # One function call should be logged
    assert len(execution_model.turns[-1].function_calls) == 1
    call = execution_model.turns[-1].function_calls[0]

    # The logged method should match the invoked expression and params should contain the resolved args
    assert call.method == "add(a, b)"
    assert call.params == '{"a": 2, "b": 3}'

    # The call result should be set and the context should contain the result variable
    assert call.result == 5
    assert execution_model.context.get_variable_value("sum_result") == 5
