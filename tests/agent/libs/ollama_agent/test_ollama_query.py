from enum import Enum

import pytest

# import the module so we can monkeypatch module-level symbols
import margarita.agent.libs.ollama_agent.ollama_agent as ollama_agent
from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.libs.ollama_agent.ollama_agent import OllamaQuery


def test_validate_model_name_should_return_enum_when_name_matches(monkeypatch):
    """
    Validate that OllamaQuery.validate_model_name returns the matching enum member when the
    provided model name matches an enum member's .value.
    """

    FakeEnum = Enum("FakeEnum", {"MODEL_A": "model-a", "MODEL_B": "model-b"})
    # Patch the module-level LLMModelEnum used inside validate_model_name
    monkeypatch.setattr(ollama_agent, "LLMModelEnum", FakeEnum)

    resolved = OllamaQuery.validate_model_name("model-b")
    assert resolved is FakeEnum.MODEL_B


def test_validate_model_name_should_raise_value_error_when_unknown(monkeypatch):
    """
    Validate that validate_model_name raises ValueError for unknown model names.
    """

    FakeEnum = Enum("FakeEnum", {"MODEL_A": "model-a"})
    monkeypatch.setattr(ollama_agent, "LLMModelEnum", FakeEnum)

    with pytest.raises(ValueError):
        OllamaQuery.validate_model_name("no-such-model")


@pytest.mark.asyncio
async def test_create_session_should_send_custom_model_when_execution_model_model_is_provided(
    monkeypatch,
):
    """
    Ensure that when ExecutionModel.metadata['model'] contains a model name, create_session
    resolves it via validate_model_name and passes the resolved value to AgentSession(..., model=...).
    """

    FakeEnum = Enum("FakeEnum", {"GEMMA_4_E2B": "gemma-4-e2b", "CUSTOM": "custom-model"})
    monkeypatch.setattr(ollama_agent, "LLMModelEnum", FakeEnum)

    captured = {}

    class FakeAgentSession:
        def __init__(
            self,
            model,
            system_message=None,
            additional_tools=None,
            on_user_input_request=None,
            on_permission_request=None,
            on_custom_tool_request=None,
        ):
            captured["model"] = model
            captured["system_message"] = system_message
            captured["additional_tools"] = additional_tools
            captured["on_user_input_request"] = on_user_input_request
            captured["on_permission_request"] = on_permission_request
            captured["on_custom_tool_request"] = on_custom_tool_request

    monkeypatch.setattr(ollama_agent, "AgentSession", FakeAgentSession)

    query = OllamaQuery(ollama_client=None)

    execution_model = ExecutionModel()
    execution_model.start_turn()

    # Simulate parser-preserved quotes around the model name (create_session strips them)
    execution_model.metadata["model"] = "'custom-model'"

    session = await query.create_session(execution_model, extra_tools=[])

    assert isinstance(session, FakeAgentSession)
    assert "model" in captured
    assert captured["model"] == FakeEnum.CUSTOM
