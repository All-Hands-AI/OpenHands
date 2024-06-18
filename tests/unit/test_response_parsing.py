import pytest

from agenthub.micro.agent import parse_response as parse_response_micro
from agenthub.monologue_agent.utils.prompts import (
    parse_action_response as parse_response_monologue,
)
from agenthub.planner_agent.prompt import parse_response as parse_response_planner
from opendevin.core.exceptions import LLMOutputError
from opendevin.core.utils.json import loads as custom_loads
from opendevin.events.action import (
    FileWriteAction,
    MessageAction,
)


@pytest.mark.parametrize(
    'parse_response_module',
    [parse_response_micro, parse_response_planner, parse_response_monologue],
)
def test_parse_single_complete_json(parse_response_module):
    input_response = """
    {
        "action": "message",
        "args": {
            "content": "The following typos were fixed:\\n* 'futur' -> 'future'\\n* 'imagin' -> 'imagine'\\n* 'techological' -> 'technological'\\n* 'responsability' -> 'responsibility'\\nThe corrected file is ./short_essay.txt."
        }
    }
    """
    expected = MessageAction(
        "The following typos were fixed:\n* 'futur' -> 'future'\n* 'imagin' -> 'imagine'\n* 'techological' -> 'technological'\n* 'responsability' -> 'responsibility'\nThe corrected file is ./short_essay.txt."
    )
    result = parse_response_module(input_response)
    assert result == expected


@pytest.mark.parametrize(
    'parse_response_module',
    [parse_response_micro, parse_response_planner, parse_response_monologue],
)
def test_parse_json_with_surrounding_text(parse_response_module):
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
    expected = FileWriteAction(
        path='./updated_file.txt', content='Updated text content here...'
    )
    result = parse_response_module(input_response)
    assert result == expected


@pytest.mark.parametrize(
    'parse_response_module',
    [parse_response_micro, parse_response_planner, parse_response_monologue],
)
def test_parse_first_of_multiple_jsons(parse_response_module):
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
    expected = FileWriteAction(path='./short_essay.txt', content='Text content here...')
    result = parse_response_module(input_response)
    assert result == expected


def test_invalid_json_raises_error():
    # This should fail if repair_json is able to fix this faulty JSON
    input_response = '{"action": "write", "args": { "path": "./short_essay.txt", "content": "Missing closing brace" }'
    with pytest.raises(LLMOutputError):
        custom_loads(input_response)


def test_no_json_found():
    input_response = 'This is just a string with no JSON object.'
    with pytest.raises(LLMOutputError):
        custom_loads(input_response)
