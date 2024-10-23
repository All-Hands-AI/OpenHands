from unittest.mock import patch

import pytest

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM
from openhands.runtime.plugins.agent_skills.file_ops.llm_integration import (
    get_file_tools_prompt,
    register_file_tools,
)
from openhands.runtime.plugins.agent_skills.file_ops.llm_tools import FileTools


@pytest.fixture
def file_ops_config():
    return LLMConfig(model='gpt-3.5-turbo', temperature=0.0, max_output_tokens=1000)


def test_supports_function_calling():
    """Test the supports_function_calling property."""
    config = LLMConfig(model='gpt-3.5-turbo')

    # Test with a model that supports function calling
    with patch('litellm.supports_function_calling', return_value=True) as mock_supports:
        llm = LLM(config)
        assert llm.config.supports_function_calling is True
        mock_supports.assert_called_once_with(model='gpt-3.5-turbo')

    # Test with a model that doesn't support function calling
    with patch(
        'litellm.supports_function_calling', return_value=False
    ) as mock_supports:
        llm = LLM(config)
        assert llm.config.supports_function_calling is False
        mock_supports.assert_called_once_with(model='gpt-3.5-turbo')


def test_supports_function_calling_with_different_models():
    """Test supports_function_calling with different model types."""
    test_cases = [
        ('gpt-4', True),
        ('gpt-3.5-turbo', True),
        ('claude-2', True),
        ('llama-2', False),
        ('mistral', False),
    ]

    for model, expected in test_cases:
        config = LLMConfig(model=model)
        with patch(
            'litellm.supports_function_calling', return_value=expected
        ) as mock_supports:
            llm = LLM(config)
            assert llm.config.supports_function_calling is expected
            mock_supports.assert_called_once_with(model=model)


@patch('openhands.llm.llm.litellm_completion')
def test_file_ops_search_functionality(mock_litellm_completion, file_ops_config):
    # Mock the LLM response with a function call
    mock_response = {
        'choices': [
            {
                'message': {
                    'content': None,
                    'function_call': {
                        'name': 'search_file',
                        'arguments': '{"file_path": "llm_tools.py", "search_term": "tool_schemas"}',
                    },
                }
            }
        ],
        'usage': {'prompt_tokens': 100, 'completion_tokens': 50},
    }
    mock_litellm_completion.return_value = mock_response

    llm = LLM(file_ops_config)
    register_file_tools(llm)

    messages = [
        {'role': 'system', 'content': get_file_tools_prompt()},
        {
            'role': 'user',
            'content': "Please search for the term 'tool_schemas' in the llm_tools.py file.",
        },
    ]

    response = llm.completion(messages=messages)

    assert mock_litellm_completion.called
    assert 'choices' in response
    assert 'message' in response['choices'][0]
    assert 'function_call' in response['choices'][0]['message']

    function_call = response['choices'][0]['message']['function_call']
    assert function_call['name'] == 'search_file'
    assert 'llm_tools.py' in function_call['arguments']
    assert 'tool_schemas' in function_call['arguments']

    call_kwargs = mock_litellm_completion.call_args[1]
    assert call_kwargs['model'] == file_ops_config.model
    assert call_kwargs['messages'] == messages
    assert call_kwargs['temperature'] == 0.0
    assert call_kwargs['max_tokens'] == 1000


def test_open_file():
    with patch(
        'openhands.runtime.plugins.agent_skills.file_ops.file_ops.open_file'
    ) as mock_open_file:

        def mock_open_file_impl(*args, **kwargs):
            print('This is the content of llm_tools.py')

        mock_open_file.side_effect = mock_open_file_impl

        file_tools = FileTools()

        result = file_tools.open_file('llm_tools.py', line_number=1, context_lines=10)
        assert 'content of llm_tools.py' in result


def test_search_file():
    with patch(
        'openhands.runtime.plugins.agent_skills.file_ops.file_ops.search_file'
    ) as mock_search_file:

        def mock_search_file_impl(*args, **kwargs):
            print('tool_schemas found in line 10')

        mock_search_file.side_effect = mock_search_file_impl

        file_tools = FileTools()

        result = file_tools.search_file('tool_schemas', file_path='llm_tools.py')
        assert 'tool_schemas' in result


def test_search_file_error():
    with patch(
        'openhands.runtime.plugins.agent_skills.file_ops.file_ops.search_file'
    ) as mock_search_file:
        mock_search_file.side_effect = FileNotFoundError('File not found')

        file_tools = FileTools()

        result = file_tools.search_file('tool_schemas', file_path='llm_tools.py')
        assert 'Error: File not found' in result


def test_search_dir():
    with patch(
        'openhands.runtime.plugins.agent_skills.file_ops.file_ops.search_dir'
    ) as mock_search_dir:

        def mock_search_dir_impl(*args, **kwargs):
            print("[Found 2 matches for 'test' in ./src]")
            print('src/file1.py (Line 10): test function')
            print('src/file2.py (Line 20): test class')
            print("[End of matches for 'test' in ./src]")

        mock_search_dir.side_effect = mock_search_dir_impl

        file_tools = FileTools()
        result = file_tools.search_dir('test', dir_path='./src')

        assert 'Found 2 matches' in result
        assert 'src/file1.py' in result
        assert 'src/file2.py' in result


def test_search_dir_error():
    with patch(
        'openhands.runtime.plugins.agent_skills.file_ops.file_ops.search_dir'
    ) as mock_search_dir:
        mock_search_dir.side_effect = PermissionError('Permission denied')

        file_tools = FileTools()
        result = file_tools.search_dir('test', dir_path='./src')

        assert 'Error: Permission denied' in result


def test_find_file():
    with patch(
        'openhands.runtime.plugins.agent_skills.file_ops.file_ops.find_file'
    ) as mock_find_file:

        def mock_find_file_impl(*args, **kwargs):
            print("[Found 2 matches for 'test.py' in ./src]")
            print('./src/test.py')
            print('./src/subdir/test.py')
            print("[End of matches for 'test.py' in ./src]")

        mock_find_file.side_effect = mock_find_file_impl

        file_tools = FileTools()
        result = file_tools.find_file('test.py', dir_path='./src')

        assert 'Found 2 matches' in result
        assert './src/test.py' in result
        assert './src/subdir/test.py' in result


def test_find_file_error():
    with patch(
        'openhands.runtime.plugins.agent_skills.file_ops.file_ops.find_file'
    ) as mock_find_file:
        mock_find_file.side_effect = PermissionError('Permission denied')

        file_tools = FileTools()
        result = file_tools.find_file('test.py', dir_path='./src')

        assert 'Error: Permission denied' in result
