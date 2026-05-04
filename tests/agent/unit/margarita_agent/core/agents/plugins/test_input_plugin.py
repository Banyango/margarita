import asyncio
from datetime import datetime

import pytest

from margarita.agent import ContentBlockType, ExecutionModel, RunStatus
from margarita.agent.core.agents.plugins.input import InputPlugin


def _create_plugin():
    return InputPlugin()


def _create_execution_model():
    model = ExecutionModel()
    model.start_turn()
    model.start_run(
        name="test",
        prompt="",
        provider="test",
        status=RunStatus.PENDING,
        start_time=datetime.now(),
    )
    return model


async def _resolve_pending_input(execution_model: ExecutionModel, answer: str) -> None:
    """Simulate the UI: wait for pending_input to appear, then resolve it."""
    while execution_model.pending_input is None:
        await asyncio.sleep(0.01)
    execution_model.pending_input.response = answer
    execution_model.pending_input.event.set()


def test_is_match_should_return_true_when_token_is_input():
    # Arrange
    plugin = _create_plugin()

    # Act
    result = plugin.is_match("input")

    # Assert
    assert result is True


def test_is_match_should_return_false_when_token_is_other():
    # Arrange
    plugin = _create_plugin()

    # Act
    result = plugin.is_match("log")

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_handle_should_store_user_input_in_variable():
    # Arrange
    plugin = _create_plugin()
    execution_model = _create_execution_model()

    # Act — run plugin and UI simulation concurrently
    await asyncio.gather(
        plugin.handle_async('"What is your name?" => user_name', execution_model=execution_model),
        _resolve_pending_input(execution_model, "Alice"),
    )

    # Assert
    assert execution_model.context.get_variable_value("user_name") == "Alice"


@pytest.mark.asyncio
async def test_handle_should_replace_variables_in_prompt_text():
    # Arrange
    plugin = _create_plugin()
    execution_model = _create_execution_model()
    execution_model.context.set_variable("topic", "Python")

    # Act
    await asyncio.gather(
        plugin.handle_async('"Tell me about ${topic}" => answer', execution_model=execution_model),
        _resolve_pending_input(execution_model, "42"),
    )

    # Assert — prompt stored on the request had the variable resolved
    # (pending_input is cleared after handle() returns; check via content block)
    blocks = execution_model.current_run.content_blocks
    assert "Python" in blocks[0].text


@pytest.mark.asyncio
async def test_handle_should_append_content_block_to_current_run():
    # Arrange
    plugin = _create_plugin()
    execution_model = _create_execution_model()

    # Act
    await asyncio.gather(
        plugin.handle_async('"Say something" => response', execution_model=execution_model),
        _resolve_pending_input(execution_model, "hello"),
    )

    # Assert
    blocks = execution_model.current_run.content_blocks
    assert len(blocks) == 2
    assert blocks[0].type == ContentBlockType.QUESTION
    assert "Say something" in blocks[0].text
    assert blocks[1].type == ContentBlockType.LOGGING
    assert "Say something" in blocks[1].text
    assert "hello" in blocks[1].text


@pytest.mark.asyncio
async def test_handle_should_clear_pending_input_after_completion():
    # Arrange
    plugin = _create_plugin()
    execution_model = _create_execution_model()

    # Act
    await asyncio.gather(
        plugin.handle_async('"Question?" => ans', execution_model=execution_model),
        _resolve_pending_input(execution_model, "yes"),
    )

    # Assert — pending_input is cleared so the UI hides the widget
    assert execution_model.pending_input is None


@pytest.mark.asyncio
async def test_handle_should_store_user_input_in_variable_when_no_prompt():
    # Arrange
    plugin = _create_plugin()
    execution_model = _create_execution_model()

    # Act
    await asyncio.gather(
        plugin.handle_async("=> result", execution_model=execution_model),
        _resolve_pending_input(execution_model, "silent answer"),
    )

    # Assert
    assert execution_model.context.get_variable_value("result") == "silent answer"


@pytest.mark.asyncio
async def test_handle_should_not_add_question_block_when_no_prompt():
    # Arrange
    plugin = _create_plugin()
    execution_model = _create_execution_model()

    # Act
    await asyncio.gather(
        plugin.handle_async("=> result", execution_model=execution_model),
        _resolve_pending_input(execution_model, "silent answer"),
    )

    # Assert — only a LOGGING block, no QUESTION block
    blocks = execution_model.current_run.content_blocks
    assert len(blocks) == 1
    assert blocks[0].type == ContentBlockType.LOGGING
    assert "silent answer" in blocks[0].text


@pytest.mark.asyncio
async def test_handle_should_raise_when_params_syntax_is_invalid():
    # Arrange
    plugin = _create_plugin()
    execution_model = _create_execution_model()

    # Act / Assert
    with pytest.raises(ValueError, match="Invalid input syntax"):
        await plugin.handle_async("missing arrow variable", execution_model=execution_model)
