from unittest.mock import AsyncMock

import pytest

from margarita.agent import ExecutionModel
from margarita.agent.core.agents.plugins.run_agent import RunAgentPlugin
from margarita.agent.core.interfaces.query_service import QueryService


def _create_mock_agent_service():
    mock_service = AsyncMock(spec=QueryService)
    return mock_service


def _create_execution_model():
    return ExecutionModel()


def test_is_match_should_return_true_when_token_is_run():
    # Arrange
    mock_service = _create_mock_agent_service()
    plugin = RunAgentPlugin(agent_service=mock_service)

    # Act
    result = plugin.is_match("run")

    # Assert
    assert result is True


def test_is_match_should_return_false_when_token_is_other():
    # Arrange
    mock_service = _create_mock_agent_service()
    plugin = RunAgentPlugin(agent_service=mock_service)

    # Act
    result = plugin.is_match("other")

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_handle_should_call_execute_query_when_called():
    # Arrange
    mock_service = _create_mock_agent_service()
    plugin = RunAgentPlugin(agent_service=mock_service)
    execution_model = _create_execution_model()

    # Act
    await plugin.handle_async("", execution_model=execution_model)

    # Assert
    mock_service.execute_query.assert_awaited_once_with(execution_model=execution_model, params="")
