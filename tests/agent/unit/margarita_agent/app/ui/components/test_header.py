import io

from rich.console import Console, Group

from margarita.agent import ExecutionModel
from margarita.agent.app.ui.components.app_header import LOGO, AppHeader


def test_build_header_should_include_logo():
    # Arrange
    header = AppHeader()
    model = ExecutionModel()
    model.start()

    # Act
    parts = header.render(model)

    assert parts[0] is LOGO


def test_build_header_should_include_warnings():
    # Arrange
    header = AppHeader()
    model = ExecutionModel()
    model.start()
    model.add_warning("something deprecated")

    # Act
    parts = header.render(model)

    # Assert
    console = Console(file=io.StringIO(), highlight=False)

    console.print(Group(*parts))
    output = console.file.getvalue()
    assert "something deprecated" in output


def test_build_header_should_include_metadata():
    # Arrange
    header = AppHeader()
    model = ExecutionModel()
    model.start()
    model.metadata["version"] = "1.2.3"

    # Act
    parts = header.render(model)

    # Assert
    console = Console(file=io.StringIO(), highlight=False)

    console.print(Group(*parts))
    output = console.file.getvalue()
    assert "version" in output
    assert "1.2.3" in output
