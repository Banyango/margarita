import json
from os.path import join

from margarita.agent import ExecutionModel
from margarita.agent.core.agents.plugins.import_plugin import ImportPlugin


def _create_execution_model():
    execution_model = ExecutionModel()
    execution_model.globals_dict = {}
    return execution_model


def test_execute_import_should_import_module_when_import_statement():
    # Arrange
    execution_model = _create_execution_model()

    # Act
    result = ImportPlugin.execute_import("import json", execution_model)

    # Assert
    assert "json" in result
    assert result["json"] is json


def test_execute_import_should_import_with_alias_when_as_used():
    # Arrange
    execution_model = _create_execution_model()

    # Act
    result = ImportPlugin.execute_import("import json as j", execution_model)

    # Assert
    assert "j" in result
    assert result["j"] is json
    assert "json" not in result


def test_execute_import_should_import_from_module_when_from_import():
    # Arrange
    execution_model = _create_execution_model()

    # Act
    result = ImportPlugin.execute_import("from os.path import join", execution_model)

    # Assert
    assert "join" in result
    assert result["join"] is join


def test_execute_import_should_add_error_when_module_not_found():
    # Arrange
    execution_model = _create_execution_model()

    # Act
    ImportPlugin.execute_import("import nonexistent_module_xyz", execution_model)

    # Assert
    assert len(execution_model.import_errors) == 1
    assert "nonexistent_module_xyz" in execution_model.import_errors[0]


def test_execute_import_should_add_error_when_invalid_statement():
    # Arrange
    execution_model = _create_execution_model()

    # Act
    ImportPlugin.execute_import("x = 1", execution_model)

    # Assert
    assert len(execution_model.import_errors) == 1
    assert "Only import statements are allowed" in execution_model.import_errors[0]
