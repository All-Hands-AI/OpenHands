import json
import os

import pytest
from litellm import ModelResponse

from openhands.agenthub.codeact_agent.function_calling import response_to_actions
from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config import AgentConfig, LLMConfig
from openhands.events.action import FileEditAction, FileReadAction, FileWriteAction
from openhands.events.event import FileEditSource, FileReadSource
from openhands.llm.llm import LLM


def create_mock_response(function_name: str, arguments: dict) -> ModelResponse:
    return ModelResponse(
        id='mock-id',
        choices=[
            {
                'message': {
                    'tool_calls': [
                        {
                            'function': {
                                'name': function_name,
                                'arguments': json.dumps(arguments),
                            },
                            'id': 'mock-tool-call-id',
                            'type': 'function',
                        }
                    ],
                    'content': None,
                    'role': 'assistant',
                },
                'index': 0,
                'finish_reason': 'tool_calls',
            }
        ],
    )


def test_gemini_tool_mapping_read_file():
    resp = create_mock_response(
        'read_file', {'path': '/abs/path/file.txt', 'offset': 2, 'limit': 5}
    )
    actions = response_to_actions(resp)
    assert len(actions) == 1
    assert isinstance(actions[0], FileReadAction)
    assert actions[0].path == '/abs/path/file.txt'
    # DEFAULT path for Gemini read
    assert actions[0].impl_source == FileReadSource.DEFAULT
    # Ensure offset/limit translated to start/end
    assert actions[0].start == 2
    assert actions[0].end == 7


def test_gemini_tool_mapping_write_file():
    resp = create_mock_response(
        'write_file', {'file_path': '/abs/path/file.txt', 'content': 'data'}
    )
    actions = response_to_actions(resp)
    assert len(actions) == 1
    assert isinstance(actions[0], FileWriteAction)
    assert actions[0].path == '/abs/path/file.txt'
    assert actions[0].content == 'data'


def test_gemini_tool_mapping_replace_defaults_expected_1():
    resp = create_mock_response(
        'replace', {
            'file_path': '/abs/path/file.txt',
            'old_string': 'a',
            'new_string': 'b',
        }
    )
    actions = response_to_actions(resp)
    assert len(actions) == 1
    a = actions[0]
    assert isinstance(a, FileEditAction)
    assert a.path == '/abs/path/file.txt'
    assert a.command == 'replace'
    assert a.impl_source == FileEditSource.OH_ACI
    assert a.old_str == 'a' and a.new_str == 'b'
    # default expected_replacements remains None here; runtime/editor should default to 1


def test_tool_exposure_gemini_models_excludes_str_replace(monkeypatch):
    # Build a dummy LLM that looks like a gemini model
    cfg = AgentConfig()
    llm = LLM(LLMConfig(model='gemini-2.5-pro'))
    agent = CodeActAgent(llm, cfg)

    # Get the tool names exposed
    tool_names = {t['function']['name'] for t in agent.tools}

    assert 'str_replace_editor' not in tool_names
    assert 'read_file' in tool_names
    assert 'write_file' in tool_names
    assert 'replace' in tool_names
