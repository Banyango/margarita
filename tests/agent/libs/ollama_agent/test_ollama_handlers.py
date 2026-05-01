from datetime import datetime

import pytest

from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.entities.content_block import ContentBlockType
from margarita.agent.entities.run import RunStatus, ToolCall
from margarita.agent.libs.ollama_agent.ollama_agent import OllamaQuery


@pytest.mark.asyncio
async def test_on_session_start_should_set_session_id_and_model_when_called():
    execution_model = ExecutionModel()
    execution_model.start_turn()
    run = execution_model.start_run(
        name="n",
        prompt="p",
        provider="p",
        status=RunStatus.RUNNING,
        start_time=datetime.now(),
    )

    query = OllamaQuery(ollama_client=None)

    metadata = type("M", (), {"id": "sess-123", "model_id": "gemma-4-e2b"})()

    await query.on_session_start(metadata, run)

    assert run.session_id == "sess-123"
    assert run.model == "gemma-4-e2b"


@pytest.mark.asyncio
async def test_on_content_delta_should_append_response_and_content_block_when_called():
    execution_model = ExecutionModel()
    execution_model.start_turn()
    run = execution_model.start_run(
        name="n",
        prompt="p",
        provider="p",
        status=RunStatus.RUNNING,
        start_time=datetime.now(),
    )

    query = OllamaQuery(ollama_client=None)

    # first delta
    await query.on_content_delta("hello", run)
    assert run.responses == ["hello"]
    assert run.content_blocks[-1].type == ContentBlockType.RESPONSE
    assert run.content_blocks[-1].text == "hello"

    # subsequent delta appends to same response
    await query.on_content_delta(" world", run)
    assert run.responses == ["hello world"]
    assert run.content_blocks[-1].text == "hello world"


@pytest.mark.asyncio
async def test_on_reasoning_delta_should_append_reasoning_and_content_block_when_called():
    execution_model = ExecutionModel()
    execution_model.start_turn()
    run = execution_model.start_run(
        name="n",
        prompt="p",
        provider="p",
        status=RunStatus.RUNNING,
        start_time=datetime.now(),
    )

    query = OllamaQuery(ollama_client=None)

    await query.on_reasoning_delta("think", run)
    assert run.reasoning == ["think"]
    assert run.content_blocks[-1].type == ContentBlockType.REASONING
    assert run.content_blocks[-1].text == "think"


@pytest.mark.asyncio
async def test_on_tool_start_should_record_tool_call_and_content_block_when_tool_is_not_ask_user():
    execution_model = ExecutionModel()
    execution_model.start_turn()
    run = execution_model.start_run(
        name="n",
        prompt="p",
        provider="p",
        status=RunStatus.RUNNING,
        start_time=datetime.now(),
    )

    query = OllamaQuery(ollama_client=None)

    metadata = type("M", (), {"name": "mytool", "tool_call_id": "tc-1", "arguments": {"x": 1}})()

    await query.on_tool_start(metadata, run)

    assert run.tool_calls
    last = run.tool_calls[-1]
    assert last.tool_call_id == "tc-1"
    assert last.tool_name == "mytool"
    assert last.arguments == {"x": 1}

    assert run.content_blocks[-1].type == ContentBlockType.TOOL_CALL
    assert run.content_blocks[-1].ref == "tc-1"


@pytest.mark.asyncio
async def test_on_tool_complete_should_update_matching_tool_call_result_and_success_when_called():
    execution_model = ExecutionModel()
    execution_model.start_turn()
    run = execution_model.start_run(
        name="n",
        prompt="p",
        provider="p",
        status=RunStatus.RUNNING,
        start_time=datetime.now(),
    )

    # Add a ToolCall that will be matched by on_tool_complete
    run.tool_calls.append(ToolCall(tool_name="mytool", tool_call_id="tc-1", arguments={"a": 1}))

    query = OllamaQuery(ollama_client=None)

    metadata = type("M", (), {"tool_call_id": "tc-1", "result": "ok", "success": True})()

    await query.on_tool_complete(metadata, run)

    assert run.tool_calls[-1].result == "ok"
    assert run.tool_calls[-1].success is True


@pytest.mark.asyncio
async def test_on_shutdown_should_set_end_time_and_mark_run_completed_when_called():
    execution_model = ExecutionModel()
    execution_model.start_turn()
    run = execution_model.start_run(
        name="n",
        prompt="p",
        provider="p",
        status=RunStatus.RUNNING,
        start_time=datetime.now(),
    )

    query = OllamaQuery(ollama_client=None)

    await query.on_shutdown(run)

    assert run.end_time is not None
    assert run.status == RunStatus.COMPLETED
