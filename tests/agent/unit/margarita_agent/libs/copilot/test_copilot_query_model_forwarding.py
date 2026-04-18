from types import SimpleNamespace

import pytest

from margarita.agent import ExecutionModel
from margarita.agent.libs.copilot.copilot_agent import CopilotQuery


class FakeSession:
    """Test double for a Copilot session used in unit tests."""

    def __init__(self):
        self._handler = None

    def on(self, handler):
        self._handler = handler
        return lambda: None

    async def send_and_wait(self, msg=None, *, prompt=None, mode=None, timeout=0):
        return SimpleNamespace(data=SimpleNamespace(content="ok"))

    async def destroy(self):
        return


class FakeCon:
    """Simple container object used in tests to mimic a connection."""

    def __init__(self):
        self.received_model = None

    async def create_session(self, config):
        # Capture the model requested
        self.received_model = getattr(config, "model", None)
        # Fallback: some objects expose attributes via __dict__
        if self.received_model is None:
            d = getattr(config, "__dict__", None)
            if isinstance(d, dict) and "model" in d:
                self.received_model = d["model"]
        return FakeSession()


class FakeClient:
    """Mock client used in unit tests to emulate Copilot client behavior."""

    def __init__(self):
        self.con = FakeCon()
        self.received_model = None

    async def create_session(self, session_config=None):
        self.received_model = getattr(session_config, "model", None)
        self.session = FakeSession()


@pytest.mark.asyncio
async def test_execute_query_forwards_model_from_execution_model(monkeypatch):
    # Arrange
    execution_model = ExecutionModel()
    # Parser currently preserves quotes around string values; ensure forwarding strips them
    execution_model.metadata = {"model": '"custom-model"'}

    fake_client = FakeClient()

    async def fake_get_variable_tool(execution_model):
        return "get_tool"

    async def fake_set_variable_tool(execution_model):
        return "set_tool"

    # Patch tool creators used by copilot_agent
    monkeypatch.setattr(
        "margarita.agent.libs.copilot.copilot_agent.create_get_variable_tool",
        fake_get_variable_tool,
    )
    monkeypatch.setattr(
        "margarita.agent.libs.copilot.copilot_agent.create_set_variable_tool",
        fake_set_variable_tool,
    )

    # Patch SessionConfig so the FakeCon can read the model attribute reliably
    class DummySessionConfig:
        def __init__(
            self,
            system_message=None,
            model=None,
            streaming=None,
            infinite_sessions=None,
            tools=None,
        ):
            self.system_message = system_message
            self.model = model
            self.streaming = streaming
            self.infinite_sessions = infinite_sessions
            self.tools = tools

    monkeypatch.setattr(
        "margarita.agent.libs.copilot.copilot_agent.SessionConfig", DummySessionConfig
    )

    query = CopilotQuery(fake_client)

    # Ensure a turn exists so start_run can attach the run
    execution_model.start_turn()

    # Act
    await query.execute_query(execution_model, params="")

    # Assert
    assert fake_client.received_model == "custom-model"
