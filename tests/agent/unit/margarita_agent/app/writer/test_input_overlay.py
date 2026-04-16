from unittest.mock import Mock

from textual.widgets import Input

from margarita.agent.app.ui.components.input_overlay import InputOverlay


def test_input_overlay_compose_yields_prompt_and_input():
    """Test that InputOverlay.compose() creates the expected widgets."""
    overlay = InputOverlay()
    widgets = list(overlay.compose())

    assert len(widgets) == 2
    assert widgets[0].id == "input-prompt"
    assert widgets[1].id == "input-field"
    assert isinstance(widgets[1], Input)


def test_input_submitted_posts_message_with_value():
    """Test that when Input.Submitted is received, InputOverlay posts a Submitted message."""
    overlay = InputOverlay()
    submitted_messages = []

    # Mock post_message to capture what gets posted
    def capture_message(msg):
        submitted_messages.append(msg)
        return True

    overlay.post_message = capture_message

    # Mock query_one to return a mock Input widget
    mock_input = Mock()
    overlay.query_one = Mock(return_value=mock_input)

    # Create a fake Input.Submitted event
    class FakeSubmittedEvent:
        def __init__(self, value):
            self.value = value

        def stop(self):
            pass

    event = FakeSubmittedEvent("test value")

    # Call the handler
    overlay._on_input_submitted(event)

    # Verify a Submitted message was posted with the correct value
    assert len(submitted_messages) == 1
    assert isinstance(submitted_messages[0], InputOverlay.Submitted)
    assert submitted_messages[0].value == "test value"

    # Verify the input was cleared
    mock_input.clear.assert_called_once()


def test_show_updates_display_and_prompt():
    """Test that show() sets display and updates the prompt."""
    overlay = InputOverlay()

    # Mock the query_one method
    mock_static = Mock()
    mock_input = Mock()

    def mock_query_one(selector, widget_type=None):
        if selector == "#input-prompt":
            return mock_static
        elif selector == "#input-field":
            return mock_input
        raise ValueError(f"Unexpected selector: {selector}")

    overlay.query_one = mock_query_one

    # Call show
    overlay.show("Enter your name:")

    # Verify display was set to True
    assert overlay.display is True

    # Verify the prompt was updated
    mock_static.update.assert_called_once_with("❯  Enter your name:")  # noqa: RUF001

    # Verify the input was focused
    mock_input.focus.assert_called_once()


def test_hide_sets_display_false():
    """Test that hide() sets display to False."""
    overlay = InputOverlay()
    overlay.display = True

    overlay.hide()

    assert overlay.display is False
