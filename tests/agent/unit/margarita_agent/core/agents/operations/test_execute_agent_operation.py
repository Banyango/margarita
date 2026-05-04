import asyncio
from pathlib import Path

import pytest

from margarita.agent import Context, ExecutionModel, Memory
from margarita.agent.core.agents.operations import execute_agent_operation as operation_module
from margarita.agent.core.agents.operations.execute_agent_operation import ExecuteAgentOperation
from margarita.agent.core.agents.services import MemoryService
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin
from margarita.agent.entities.prompt_integrity import PromptUnverifiedPathError


class MockMemoryService(MemoryService):
    async def save_memory(self, memory: Memory):
        pass

    async def load_memory(self, context: Context) -> Memory:
        return Memory(context)


class MockPlugin(AgentPlugin):
    """Mock plugin for testing."""

    def __init__(self, token: str):
        self.token = token
        self.handle_called = False
        self.handle_params = None

    def is_match(self, token: str) -> bool:
        return token == self.token

    async def handle_async(self, params: str, execution_model: ExecutionModel):
        self.handle_called = True
        self.handle_params = params


class AlwaysUnverifiedIntegrity:
    def __init__(self):
        self.verify_bytes_calls = 0

    def verify_trusted_path(self, path):
        raise PromptUnverifiedPathError("outside trusted root")

    def verify_bytes(self, path, content_bytes):
        self.verify_bytes_calls += 1


class AlwaysTrustedIntegrity:
    def __init__(self):
        self.verify_trusted_path_calls = 0
        self.verify_bytes_calls = 0
        self.last_verified_path = None
        self.last_verified_bytes = b""

    def verify_trusted_path(self, path):
        self.verify_trusted_path_calls += 1

    def verify_bytes(self, path, content_bytes):
        self.verify_bytes_calls += 1
        self.last_verified_path = path
        self.last_verified_bytes = content_bytes


class FakeIncludeNode:
    def __init__(self, template_name: str):
        self.template_name = template_name
        self.params = {}


class FakeParser:
    def parse(self, content: str):
        return {}, []


def _create_execution_model():
    return ExecutionModel()


def _create_operation(
    plugins: list[AgentPlugin] | None = None,
    tmp_path: Path | None = None,
    prompt_integrity=None,
    allow_unverified: bool = False,
):
    if plugins is None:
        plugins = []

    execution_model = _create_execution_model()

    operation = ExecuteAgentOperation(
        plugins=plugins,
        execution_model=execution_model,
        memory_service=MockMemoryService(),
        prompt_integrity=prompt_integrity,
        allow_unverified=allow_unverified,
    )

    if tmp_path:
        operation.base_path = tmp_path

    return operation


def _patch_include_parser(monkeypatch):
    """Patch parser/include node classes to isolate include execution behavior."""
    monkeypatch.setattr(operation_module, "IncludeNode", FakeIncludeNode)
    monkeypatch.setattr(operation_module, "Parser", FakeParser)


# --- Upstream Tests ---


@pytest.mark.asyncio
async def test_execute_async_should_parse_and_process_text_node_when_given_text():
    # Arrange
    operation = _create_operation()
    mgx_content = """---
description: "Test file"
---

<<
Hello, World!
>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "Hello, World!\n"
    assert operation.execution_model.metadata == {"description": '"Test file"'}


@pytest.mark.asyncio
async def test_execute_async_parses_model_field_in_metadata():
    # Arrange
    operation = _create_operation()
    mgx_content = """---
model: "custom-model"
---
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.metadata == {"model": '"custom-model"'}


@pytest.mark.asyncio
async def test_execute_async_should_replace_variables_in_text_when_variable_exists():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("name", "Alice")
    mgx_content = """<<
Hello, ${name}!
>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "Hello, Alice!\n"


@pytest.mark.asyncio
async def test_execute_async_should_handle_state_node_when_state_defined():
    # Arrange
    operation = _create_operation()
    mgx_content = """@state my_var = "test_value"
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.get_variable_value("my_var") == "test_value"


@pytest.mark.asyncio
async def test_execute_async_should_handle_state_with_number_when_state_defined():
    # Arrange
    operation = _create_operation()
    mgx_content = """@state counter = 42
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.get_variable_value("counter") == 42


@pytest.mark.asyncio
async def test_execute_async_should_handle_state_with_list_when_state_defined():
    # Arrange
    operation = _create_operation()
    mgx_content = """@state items = ["apple", "banana", "cherry"]
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.get_variable_value("items") == [
        "apple",
        "banana",
        "cherry",
    ]


@pytest.mark.asyncio
async def test_execute_async_should_process_for_loop_when_iterating_over_list():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("items", ["a", "b", "c"])
    mgx_content = """for item in items:
    <<Item: ${item}>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "Item: a\nItem: b\nItem: c\n"


@pytest.mark.asyncio
async def test_execute_async_should_break_for_loop_when_break_statement_encountered():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("items", ["a", "b", "c", "d", "e"])
    mgx_content = """
for item in items:
    <<Item: ${item}>>
    if item == "c":
        break
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    # Should only process items a, b, and c, then break
    assert operation.execution_model.context.window == "Item: a\nItem: b\nItem: c\n"


@pytest.mark.asyncio
async def test_execute_async_should_handle_if_node_when_condition_is_true():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("is_active", True)
    mgx_content = """if is_active:
    <<Active>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "Active\n"


@pytest.mark.asyncio
async def test_execute_async_should_skip_if_block_when_condition_is_false():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("is_active", False)
    mgx_content = """if is_active:
    <<Active>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == ""


@pytest.mark.asyncio
async def test_execute_async_should_render_if_block_when_condition_is_lowercase_true_literal():
    # Arrange
    operation = _create_operation()
    mgx_content = """if true:
    <<Active>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "Active\n"


@pytest.mark.asyncio
async def test_execute_async_should_skip_if_block_when_condition_is_lowercase_false_literal():
    # Arrange
    operation = _create_operation()
    mgx_content = """if false:
    <<Active>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == ""


@pytest.mark.asyncio
async def test_execute_async_should_call_plugin_when_effect_matches():
    # Arrange
    mock_plugin = MockPlugin("test")
    operation = _create_operation(plugins=[mock_plugin])
    mgx_content = """@effect test param1 param2
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert mock_plugin.handle_called is True
    assert mock_plugin.handle_params == "param1 param2"


@pytest.mark.asyncio
async def test_execute_async_should_not_call_plugin_when_effect_does_not_match():
    # Arrange
    mock_plugin = MockPlugin("other")
    operation = _create_operation(plugins=[mock_plugin])
    mgx_content = """@effect test param1
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert mock_plugin.handle_called is False


@pytest.mark.asyncio
async def test_execute_async_should_handle_include_when_file_exists(tmp_path):
    # Arrange
    operation = _create_operation()

    # Create a temporary .mg file
    include_file = tmp_path / "include.mg"
    include_file.write_text("<<Included content>>")

    mgx_content = """[[ include.mg ]]"""

    # Act
    await operation.execute_async(mgx_content, base_path=tmp_path)

    # Assert
    assert operation.execution_model.context.window == "Included content\n"


@pytest.mark.asyncio
async def test_execute_async_should_skip_include_when_file_does_not_exist(tmp_path):
    # Arrange
    operation = _create_operation()
    mgx_content = """[[ nonexistent.mg ]]
"""

    # Act
    with pytest.raises(FileNotFoundError, match="Included prompt file was not found"):
        await operation.execute_async(mgx_content, base_path=tmp_path)

    # Assert
    # assert operation.execution_model.context.window == ""


@pytest.mark.asyncio
async def test_execute_async_should_start_turn_when_executed():
    # Arrange
    operation = _create_operation()
    mgx_content = """<<Test>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert len(operation.execution_model.turns) == 1


@pytest.mark.asyncio
async def test_is_truthy_should_return_true_when_value_is_true():
    # Arrange
    operation = _create_operation()

    # Act & Assert
    assert operation._is_truthy(True) is True
    assert operation._is_truthy("text") is True
    assert operation._is_truthy([1, 2, 3]) is True
    assert operation._is_truthy({"key": "value"}) is True
    assert operation._is_truthy(42) is True
    assert operation._is_truthy(1.5) is True


@pytest.mark.asyncio
async def test_is_truthy_should_return_false_when_value_is_falsy():
    # Arrange
    operation = _create_operation()

    # Act & Assert
    assert operation._is_truthy(False) is False
    assert operation._is_truthy(None) is False
    assert operation._is_truthy("") is False
    assert operation._is_truthy([]) is False
    assert operation._is_truthy({}) is False
    assert operation._is_truthy(0) is False
    assert operation._is_truthy(0.0) is False


@pytest.mark.asyncio
async def test_execute_plugin_should_call_matching_plugin_when_plugin_matches():
    # Arrange
    mock_plugin = MockPlugin("run")
    operation = _create_operation(plugins=[mock_plugin])

    # Act
    await operation._execute_plugin_async(plugin="run", operation="run")

    # Assert
    assert mock_plugin.handle_called is True
    assert mock_plugin.handle_params == "run"


@pytest.mark.asyncio
async def test_execute_plugin_should_not_call_plugin_when_no_match():
    # Arrange
    mock_plugin = MockPlugin("run")
    operation = _create_operation(plugins=[mock_plugin])

    # Act
    await operation._execute_plugin_async(plugin="other", operation="run")

    # Assert
    assert mock_plugin.handle_called is False


@pytest.mark.asyncio
async def test_execute_async_should_handle_variable_node_when_variable_exists():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("greeting", "Hi there")
    mgx_content = """<<${greeting}>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "Hi there\n"


@pytest.mark.asyncio
async def test_execute_async_should_handle_nested_for_loops():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("outer", [1, 2])
    operation.execution_model.context.set_variable("inner", ["a", "b"])
    mgx_content = """for x in outer:
    for y in inner:
        <<${x}${y} >>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "1a\n1b\n2a\n2b\n"


@pytest.mark.asyncio
async def test_execute_async_should_break_inner_loop_only_when_break_in_nested_loop():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("outer", [1, 2, 3])
    operation.execution_model.context.set_variable("inner", ["a", "b", "c"])
    mgx_content = """
for x in outer:
    <<Outer: ${x}>>
    for y in inner:
        <<${x}${y} >>
        if y == "b":
            break
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    # Each outer iteration should process inner a and b, then break
    # All three outer iterations should complete
    expected = "Outer: 1\n1a\n1b\nOuter: 2\n2a\n2b\nOuter: 3\n3a\n3b\n"
    assert operation.execution_model.context.window == expected


@pytest.mark.asyncio
async def test_execute_async_should_break_immediately_when_break_at_start_of_loop():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("items", ["a", "b", "c"])
    mgx_content = """
for item in items:
    break
    <<Item: ${item}>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    # Should break before processing any items
    assert operation.execution_model.context.window == ""


@pytest.mark.asyncio
async def test_execute_async_should_process_import_node_when_import_present():
    # Arrange
    operation = _create_operation()
    mgx_content = """from math import sqrt
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert len(operation.execution_model.turns) == 1


@pytest.mark.asyncio
async def test_execute_async_should_handle_complex_mgx_file():
    # Arrange
    mock_plugin = MockPlugin("run")
    operation = _create_operation(plugins=[mock_plugin])
    operation.execution_model.context.set_variable("items", ["apple", "banana"])

    mgx_content = """---
description: "Complex test"
author: "Test"
---

@state count = 0

<<Processing items:>>

for item in items:
    <<
    - ${item}
    >>

@effect run
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.metadata == {
        "description": '"Complex test"',
        "author": '"Test"',
    }
    assert operation.execution_model.context.get_variable_value("count") == 0
    assert "Processing items:" in operation.execution_model.context.window
    assert "- apple" in operation.execution_model.context.window
    assert "- banana" in operation.execution_model.context.window
    assert mock_plugin.handle_called is True


# --- Prompt Integrity Tests (Feature Branch) ---


def test_normalize_include_path_should_append_mg_extension_when_extension_is_missing():
    # Arrange
    sut = _create_operation()

    # Act
    result = sut._normalize_include_path("salt/use-uv/use-uv")

    # Assert
    assert result == "salt/use-uv/use-uv.mg"


def test_normalize_include_path_should_raise_value_error_when_extension_is_not_supported():
    # Arrange
    sut = _create_operation()

    # Act
    # Assert
    with pytest.raises(ValueError, match="Unsupported include extension"):
        sut._normalize_include_path("salt/setup.txt")


def test_process_nodes_async_should_execute_false_block_when_if_condition_is_false(monkeypatch):
    # Arrange
    class FakeTextNode:
        def __init__(self, content: str):
            self.content = content

    class FakeIfNode:
        def __init__(self, condition: str, true_block: list, false_block: list):
            self.condition = condition
            self.true_block = true_block
            self.false_block = false_block

    monkeypatch.setattr(operation_module, "TextNode", FakeTextNode)
    monkeypatch.setattr(operation_module, "IfNode", FakeIfNode)

    execution_model = _create_execution_model()
    execution_model.context.set_variable("feature_enabled", False)

    sut = ExecuteAgentOperation(
        plugins=[],
        execution_model=execution_model,
        memory_service=MockMemoryService(),
    )

    if_node = FakeIfNode(
        condition="feature_enabled",
        true_block=[FakeTextNode("TRUE")],
        false_block=[FakeTextNode("FALSE")],
    )

    # Act
    asyncio.run(sut._process_nodes_async([if_node]))

    # Assert
    assert execution_model.context.window == "FALSE"


def test_process_nodes_async_should_raise_unverified_path_error_when_unverified_include_is_disallowed(
    monkeypatch, tmp_path
):
    # Arrange
    _patch_include_parser(monkeypatch)

    include_file = tmp_path / "external.mg"
    include_file.write_text("<<external>>")

    sut = _create_operation(
        tmp_path=tmp_path,
        prompt_integrity=AlwaysUnverifiedIntegrity(),
        allow_unverified=False,
    )

    # Act
    # Assert
    with pytest.raises(PromptUnverifiedPathError):
        asyncio.run(sut._process_nodes_async([FakeIncludeNode("external")]))


def test_process_nodes_async_should_raise_file_not_found_error_when_include_file_is_missing(
    monkeypatch, tmp_path
):
    # Arrange
    _patch_include_parser(monkeypatch)
    sut = _create_operation(tmp_path=tmp_path)

    # Act
    # Assert
    with pytest.raises(FileNotFoundError, match="Included prompt file was not found"):
        asyncio.run(sut._process_nodes_async([FakeIncludeNode("does-not-exist")]))


def test_process_nodes_async_should_skip_hash_verification_when_unverified_include_is_allowed(
    monkeypatch, tmp_path
):
    # Arrange
    _patch_include_parser(monkeypatch)

    include_file = tmp_path / "external.mg"
    include_file.write_text("<<external>>")
    warning_messages = []

    def _fake_warning(message: str, *args, **kwargs):
        warning_messages.append(message.format(*args))

    monkeypatch.setattr(operation_module.logger, "warning", _fake_warning)

    integrity = AlwaysUnverifiedIntegrity()
    sut = _create_operation(
        tmp_path=tmp_path,
        prompt_integrity=integrity,
        allow_unverified=True,
    )

    # Act
    asyncio.run(sut._process_nodes_async([FakeIncludeNode("external")]))

    # Assert
    assert integrity.verify_bytes_calls == 0
    assert len(warning_messages) == 1
    assert "Allowing unverified include outside trusted prompt root" in warning_messages[0]
    assert str(include_file.resolve(strict=False)) in warning_messages[0]
    assert "outside trusted root" in warning_messages[0]


def test_process_nodes_async_should_verify_trusted_include_when_include_is_in_trusted_root(
    monkeypatch, tmp_path
):
    # Arrange
    _patch_include_parser(monkeypatch)

    include_file = tmp_path / "trusted.mg"
    include_file.write_text("<<trusted>>")

    integrity = AlwaysTrustedIntegrity()
    sut = _create_operation(
        tmp_path=tmp_path,
        prompt_integrity=integrity,
        allow_unverified=False,
    )

    # Act
    asyncio.run(sut._process_nodes_async([FakeIncludeNode("trusted")]))

    # Assert
    assert integrity.verify_trusted_path_calls == 1
    assert integrity.verify_bytes_calls == 1
    assert str(integrity.last_verified_path) == str(include_file.resolve(strict=False))
    assert integrity.last_verified_bytes == b"<<trusted>>"


def test_process_nodes_async_should_raise_error_when_included_prompt_content_is_malformed(
    monkeypatch, tmp_path
):
    # Arrange
    class RaisingParser:
        def parse(self, content: str):
            raise ValueError("Malformed include prompt content")

    monkeypatch.setattr(operation_module, "IncludeNode", FakeIncludeNode)
    monkeypatch.setattr(operation_module, "Parser", RaisingParser)

    include_file = tmp_path / "trusted.mg"
    include_file.write_text("<<broken>>")
    sut = _create_operation(tmp_path=tmp_path)

    # Act
    # Assert
    with pytest.raises(ValueError, match="Malformed include prompt content"):
        asyncio.run(sut._process_nodes_async([FakeIncludeNode("trusted")]))


def test_process_nodes_async_should_raise_unicode_decode_error_when_include_file_is_not_utf8(
    monkeypatch, tmp_path
):
    # Arrange
    _patch_include_parser(monkeypatch)
    binary_include_file = tmp_path / "binary.mg"
    binary_include_file.write_bytes(b"\xff")
    sut = _create_operation(tmp_path=tmp_path)

    # Act
    # Assert
    with pytest.raises(UnicodeDecodeError):
        asyncio.run(sut._process_nodes_async([FakeIncludeNode("binary")]))


def test_process_nodes_async_should_resolve_include_params_from_context_not_use_literal_variable_name(
    monkeypatch, tmp_path
):
    # Arrange — include file uses ${input} which should receive the resolved value
    include_file = tmp_path / "child.mg"
    include_file.write_text("<<${input}>>")

    # Only patch IncludeNode so isinstance checks use FakeIncludeNode;
    # leave Parser unpatcheed so the real parser processes the include file.
    monkeypatch.setattr(operation_module, "IncludeNode", FakeIncludeNode)

    execution_model = _create_execution_model()
    execution_model.context.set_variable("userInput", "a calculator app")

    sut = ExecuteAgentOperation(
        plugins=[], execution_model=execution_model, memory_service=MockMemoryService()
    )
    sut.base_path = tmp_path

    include_node = FakeIncludeNode("child")
    include_node.params = {"input": "userInput"}

    # Act
    asyncio.run(sut._process_nodes_async([include_node]))

    # Assert — context window should contain the resolved value, not the literal "userInput"
    assert "a calculator app" in execution_model.context.window
    assert "userInput" not in execution_model.context.window


@pytest.mark.asyncio
async def test_execute_async_should_process_for_loop_when_iterating_over_dict():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("person", {"name": "Alice", "role": "admin"})
    mgx_content = """for key, value in person:
    <<${key}: ${value}>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert "name: Alice\n" in operation.execution_model.context.window
    assert "role: admin\n" in operation.execution_model.context.window


@pytest.mark.asyncio
async def test_execute_async_should_process_for_loop_when_iterating_over_dict_with_break():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("data", {"a": 1, "b": 2, "c": 3})
    mgx_content = """for key, value in data:
    <<${key}: ${value}>>
    if key == "b":
        break
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert "a: 1\n" in operation.execution_model.context.window
    assert "b: 2\n" in operation.execution_model.context.window
    assert "c: 3\n" not in operation.execution_model.context.window


@pytest.mark.asyncio
async def test_execute_async_should_run_all_effects_in_parallel_when_await_all():
    # Arrange
    call_order = []

    class TrackingPlugin(AgentPlugin):
        def __init__(self, token: str):
            self.token = token

        def is_match(self, t: str) -> bool:
            return t == self.token

        async def handle_async(self, params: str, execution_model: ExecutionModel):
            call_order.append(self.token)

    plugin_a = TrackingPlugin("alpha")
    plugin_b = TrackingPlugin("beta")
    operation = _create_operation(plugins=[plugin_a, plugin_b])
    mgx_content = """@await-all
    @effect alpha
    @effect beta
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert — both effects were called
    assert "alpha" in call_order
    assert "beta" in call_order


@pytest.mark.asyncio
async def test_await_all_partial_failure_logs_error_and_keeps_successful_outputs():
    # Arrange
    results = []

    class SuccessPlugin(AgentPlugin):
        def is_match(self, t: str) -> bool:
            return t == "good"

        async def handle_async(self, params: str, execution_model: ExecutionModel):
            results.append("good")
            execution_model.context.set_variable("goodResult", "ok")

    class FailPlugin(AgentPlugin):
        def is_match(self, t: str) -> bool:
            return t == "bad"

        async def handle_async(self, params: str, execution_model: ExecutionModel):
            raise RuntimeError("child exploded")

    operation = _create_operation(plugins=[SuccessPlugin(), FailPlugin()])
    mgx_content = """@await-all
    @effect good
    @effect bad
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert — successful sibling ran
    assert "good" in results
    # Assert — failure was logged as a content block (not re-raised)
    log_texts = [
        cb.text
        for cb in operation.execution_model.current_turn.content_blocks
        if "[AwaitAll]" in (cb.text or "")
    ]
    assert any("child exploded" in t for t in log_texts)
    # Assert — successful output is still present
    assert operation.execution_model.context.get_variable_value("goodResult") == "ok"


@pytest.mark.asyncio
async def test_execute_async_should_call_all_await_all_effects_regardless_of_order():
    # Arrange
    handled = []

    class CollectingPlugin(AgentPlugin):
        def __init__(self, token: str):
            self.token = token

        def is_match(self, t: str) -> bool:
            return t == self.token

        async def handle_async(self, params: str, execution_model: ExecutionModel):
            handled.append((self.token, params))

    plugin_x = CollectingPlugin("x")
    plugin_y = CollectingPlugin("y")
    operation = _create_operation(plugins=[plugin_x, plugin_y])
    mgx_content = """@await-all
    @effect x foo
    @effect y bar
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert ("x", "foo") in handled
    assert ("y", "bar") in handled
