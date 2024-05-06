import pytest
from agenthub.micro.agent import parse_response, LLMOutputError
from opendevin.events.action import (
    AgentThinkAction,
    FileWriteAction,
)


def test_parse_single_complete_json():
    input_response = """
    {
        "action": "think",
        "args": {
            "thought": "The following typos were fixed:\\n* 'futur' -> 'future'\\n* 'imagin' -> 'imagine'\\n* 'techological' -> 'technological'\\n* 'responsability' -> 'responsibility'\\nThe corrected file is ./short_essay.txt."
        }
    }
    """
    expected = AgentThinkAction(thought="The following typos were fixed:\n* 'futur' -> 'future'\n* 'imagin' -> 'imagine'\n* 'techological' -> 'technological'\n* 'responsability' -> 'responsibility'\nThe corrected file is ./short_essay.txt.")
    assert parse_response(input_response) == expected


def test_parse_json_with_surrounding_text():
    input_response = """
    Some initial text that is not JSON formatted.
    {
        "action": "write",
        "args": {
            "path": "./updated_file.txt",
            "content": "Updated text content here..."
        }
    }
    Some trailing text that is also not JSON formatted.
    """
    expected = FileWriteAction(path="./updated_file.txt", content="Updated text content here...")
    assert parse_response(input_response) == expected


def test_parse_first_of_multiple_jsons():
    input_response = """
    I will firstly do
    {
        "action": "write",
        "args": {
            "path": "./short_essay.txt",
            "content": "Text content here..."
        }
    }
    Then I will continue with
    {
        "action": "think",
        "args": {
            "thought": "This should not be parsed."
        }
    }
    """
    expected = FileWriteAction(path="./short_essay.txt", content="Text content here...")
    assert parse_response(input_response) == expected


def test_invalid_json_raises_error():
    input_response = '{"action": "write", "args": { "path": "./short_essay.txt", "content": "Missing closing brace"'
    with pytest.raises(LLMOutputError):
        parse_response(input_response)
