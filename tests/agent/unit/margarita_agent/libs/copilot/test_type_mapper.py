import pytest

from margarita.agent.libs.copilot.type_mapper import map_type


@pytest.mark.parametrize(
    "input_type, expected",
    [
        ("str", "string"),
        ("string", "string"),
        ("int", "integer"),
        ("integer", "integer"),
        ("float", "number"),
        ("number", "number"),
        ("bool", "boolean"),
        ("boolean", "boolean"),
        ("list", "array"),
        ("array", "array"),
        ("dict", "object"),
        ("object", "object"),
    ],
)
def test_map_type_should_return_correct_json_type_when_string_provided(input_type, expected):
    # Arrange / Act
    result = map_type(input_type)

    # Assert
    assert result == expected


def test_map_type_should_return_string_when_unknown_type():
    # Arrange
    unknown = "datetime"

    # Act
    result = map_type(unknown)

    # Assert
    assert result == "string"


@pytest.mark.parametrize(
    "type_obj, expected",
    [
        (str, "string"),
        (int, "integer"),
        (float, "number"),
        (bool, "boolean"),
        (list, "array"),
        (dict, "object"),
    ],
)
def test_map_type_should_handle_type_objects_when_passed(type_obj, expected):
    # Arrange / Act
    result = map_type(type_obj)

    # Assert
    assert result == expected
