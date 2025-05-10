import pytest
from prompt_toolkit.widgets import TextArea

from openhands.cli.tui import (
    ENABLE_STREAMING,
    initialize_streaming_output,
    update_streaming_output,
    streaming_output_text_area,
)

class MockTextArea:
    def __init__(self, **kwargs):
        self.text = ""
        self.buffer = self
        self.cursor_position = 0

    def __str__(self):
        return self.text

class MockFrame:
    def __init__(self, content, **kwargs):
        self.content = content

def test_streaming_output(monkeypatch):
    # Ensure streaming is enabled
    monkeypatch.setattr('openhands.cli.tui.ENABLE_STREAMING', True)
    # Mock the print functions to prevent actual printing
    monkeypatch.setattr('openhands.cli.tui.print_container', lambda _: None)
    monkeypatch.setattr('openhands.cli.tui.print_formatted_text', lambda _: None)

    # Create mock widgets
    monkeypatch.setattr('openhands.cli.tui.TextArea', MockTextArea)
    monkeypatch.setattr('openhands.cli.tui.Frame', MockFrame)

    # Initialize streaming output
    initialize_streaming_output()

    # Get the global variable from the module
    import openhands.cli.tui
    text_area = openhands.cli.tui.streaming_output_text_area
    assert text_area is not None
    assert isinstance(text_area, MockTextArea)
    assert text_area.text == ""

    # Test updating with single line
    update_streaming_output("Hello")
    assert text_area.text == "Hello"

    # Test appending more text
    update_streaming_output(" World")
    assert text_area.text == "Hello World"

    # Test multiline output
    update_streaming_output("\nNew line")
    assert text_area.text == "Hello World\nNew line"
