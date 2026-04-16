import pytest

from margarita.agent import ExecutionModel
from margarita.agent.core.agents.plugins.context import ContextPlugin


def _create_plugin():
    return ContextPlugin()


def _create_execution_model():
    return ExecutionModel()


def test_is_match_should_return_true_when_token_is_context():
    # Arrange
    plugin = _create_plugin()

    # Act
    result = plugin.is_match("context")

    # Assert
    assert result is True


def test_is_match_should_return_false_when_token_is_other():
    # Arrange
    plugin = _create_plugin()

    # Act
    result = plugin.is_match("other")

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_handle_should_clear_context_when_params_is_clear():
    # Arrange
    execution_model = _create_execution_model()
    execution_model.context.add_to_context_window("some content")
    plugin = _create_plugin()

    # Act
    await plugin.handle("clear", execution_model=execution_model)

    # Assert
    assert execution_model.context.window == ""


@pytest.mark.asyncio
async def test_handle_should_not_clear_when_params_is_not_clear():
    # Arrange
    execution_model = _create_execution_model()
    execution_model.context.add_to_context_window("some content")
    plugin = _create_plugin()

    # Act
    await plugin.handle("something_else", execution_model=execution_model)

    # Assert
    assert execution_model.context.window == "some content"
