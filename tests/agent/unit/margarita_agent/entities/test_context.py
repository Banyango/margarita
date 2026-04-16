from margarita.agent.entities.context import Context
from margarita.agent.entities.tool import Param, Tool


def _create_context() -> Context:
    return Context()


def _create_tool(name: str = "test_tool") -> Tool:
    return Tool(
        name=name,
        params=[Param(name="arg1", type="str")],
        return_types=["str"],
    )


def test_add_to_context_window_should_append_content_when_called():
    # Arrange
    context = _create_context()

    # Act
    context.add_to_context_window("Hello ")
    context.add_to_context_window("World")

    # Assert
    assert context.window == "Hello World"


def test_get_variable_value_should_return_value_when_key_exists():
    # Arrange
    context = _create_context()
    context.data["greeting"] = "hello"

    # Act
    result = context.get_variable_value("greeting")

    # Assert
    assert result == "hello"


def test_get_variable_value_should_return_none_when_key_missing():
    # Arrange
    context = _create_context()

    # Act
    result = context.get_variable_value("nonexistent")

    # Assert
    assert result is None


def test_get_variable_value_should_resolve_dotted_notation_when_nested_dict():
    # Arrange
    context = _create_context()
    context.data["user"] = {"name": "Alice", "address": {"city": "Seattle"}}

    # Act
    name = context.get_variable_value("user.name")
    city = context.get_variable_value("user.address.city")

    # Assert
    assert name == "Alice"
    assert city == "Seattle"


def test_get_variable_value_should_return_range_list_when_range_expression():
    # Arrange
    context = _create_context()

    # Act
    result_single = context.get_variable_value("range(5)")
    result_start_stop = context.get_variable_value("range(1, 4)")
    result_step = context.get_variable_value("range(0, 10, 2)")

    # Assert
    assert result_single == [0, 1, 2, 3, 4]
    assert result_start_stop == [1, 2, 3]
    assert result_step == [0, 2, 4, 6, 8]


def test_get_variable_value_should_return_none_when_invalid_range():
    # Arrange
    context = _create_context()

    # Act
    result_empty = context.get_variable_value("range()")
    result_bad = context.get_variable_value("range(abc)")

    # Assert
    assert result_empty is None
    assert result_bad is None


def test_get_variable_value_should_resolve_variables_in_range_arguments():
    # Arrange
    context = _create_context()
    context.set_variable("n", 3)
    context.set_variable("start", 2)
    context.set_variable("end", 5)

    # Act
    result_single = context.get_variable_value("range(n)")
    result_start_end = context.get_variable_value("range(start, end)")

    # Assert
    assert result_single == [0, 1, 2]
    assert result_start_end == [2, 3, 4]


def test_get_variable_value_should_handle_zero_and_negative_ranges():
    # Arrange
    context = _create_context()
    context.set_variable("zero", 0)
    context.set_variable("neg", -2)
    context.set_variable("start_neg", -3)
    context.set_variable("end_neg", 1)

    # Act
    result_zero = context.get_variable_value("range(zero)")
    result_neg = context.get_variable_value("range(neg)")
    result_start_end_neg = context.get_variable_value("range(start_neg, end_neg)")

    # Assert
    assert result_zero == []
    # Python's range(-2) produces [] because start=0 stop=-2 is empty
    assert result_neg == []
    assert result_start_end_neg == [-3, -2, -1, 0]


def test_get_variable_value_should_return_none_when_range_variable_missing_or_not_int():
    # Arrange
    context = _create_context()
    context.set_variable("bad", "not_an_int")

    # Act
    result_missing = context.get_variable_value("range(missing)")
    result_bad = context.get_variable_value("range(bad)")

    # Assert
    assert result_missing is None
    assert result_bad is None


def test_get_variable_value_should_return_indexed_item_when_bracket_notation():
    # Arrange
    context = _create_context()
    context.data["items"] = ["a", "b", "c", "d"]

    # Act
    result = context.get_variable_value("items[1]")

    # Assert
    assert result == "b"


def test_get_variable_value_should_return_slice_when_slice_notation():
    # Arrange
    context = _create_context()
    context.data["items"] = ["a", "b", "c", "d", "e"]

    # Act
    result = context.get_variable_value("items[0:3]")

    # Assert
    assert result == ["a", "b", "c"]


def test_get_variable_value_should_return_none_when_index_out_of_bounds():
    # Arrange
    context = _create_context()
    context.data["items"] = ["a", "b"]

    # Act
    result = context.get_variable_value("items[10]")

    # Assert
    assert result is None


def test_set_variable_should_store_value_when_called():
    # Arrange
    context = _create_context()

    # Act
    context.set_variable("count", 42)

    # Assert
    assert context.data["count"] == 42


def test_add_to_state_should_update_data_when_called():
    # Arrange
    context = _create_context()

    # Act
    context.add_to_state("current_item", {"id": 1})

    # Assert
    assert context.data["current_item"] == {"id": 1}


def test_remove_from_state_should_delete_key_when_exists():
    # Arrange
    context = _create_context()
    context.data["temp"] = "value"

    # Act
    context.remove_from_state("temp")

    # Assert
    assert "temp" not in context.data


def test_remove_from_state_should_not_error_when_key_missing():
    # Arrange
    context = _create_context()

    # Act / Assert - should not raise
    context.remove_from_state("nonexistent")


def test_add_tool_should_append_tool_when_called():
    # Arrange
    context = _create_context()
    tool = _create_tool("my_tool")

    # Act
    context.add_tool(tool)

    # Assert
    assert len(context.tools) == 1
    assert context.tools[0].name == "my_tool"


def test_clear_tools_should_remove_all_tools_when_called():
    # Arrange
    context = _create_context()
    context.tools = [_create_tool("a"), _create_tool("b")]

    # Act
    context.clear_tools()

    # Assert
    assert context.tools == []


def test_clear_context_should_reset_window_when_called():
    # Arrange
    context = _create_context()
    context.window = "some content"

    # Act
    context.clear_context()

    # Assert
    assert context.window == ""


def test_replace_variables_in_content_should_replace_simple_variable():
    # Arrange
    context = _create_context()
    context.set_variable("name", "Bob")

    # Act
    result = context.replace_variables_in_content("Hello, ${name}!")

    # Assert
    assert result == "Hello, Bob!"


def test_replace_variables_in_content_should_replace_nested_variable():
    # Arrange
    context = _create_context()
    context.set_variable("user", {"name": "Charlie"})

    # Act
    result = context.replace_variables_in_content("Hello, ${user.name}!")

    # Assert
    assert result == "Hello, Charlie!"


def test_replace_variables_in_content_should_replace_with_empty_when_variable_not_found():
    # Arrange
    context = _create_context()

    # Act
    result = context.replace_variables_in_content("Hello, ${unknown}!")

    # Assert
    assert result == "Hello, !"


def test_replace_variables_in_content_should_replace_multiple_variables():
    # Arrange
    context = _create_context()
    context.set_variable("first", "John")
    context.set_variable("last", "Doe")

    # Act
    result = context.replace_variables_in_content("Name: ${first} ${last}")

    # Assert
    assert result == "Name: John Doe"


def test_replace_variables_in_content_should_leave_malformed_placeholder_unchanged():
    # Arrange
    context = _create_context()

    # Act
    result = context.replace_variables_in_content("Value: ${1invalid}")

    # Assert
    assert result == "Value: ${1invalid}"
