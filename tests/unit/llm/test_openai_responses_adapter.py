import time
from unittest.mock import patch

import pytest

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM


class DummyResponses:
    def __init__(self, with_tool: bool = False):
        self.id = 'resp-123'
        self.model = 'gpt-5'
        self.created = int(time.time())
        self.output_text = 'Final answer'
        # Build output with reasoning and text fragments
        self.output = [
            {'type': 'reasoning', 'text': 'I will think step by step.'},
            {
                'type': 'message',
                'content': [
                    {'type': 'output_text', 'text': 'Final answer'},
                ],
            },
        ]
        if with_tool:
            self.output.append(
                {
                    'type': 'tool_call',
                    'name': 'do_something',
                    'arguments': {'x': 1},
                    'id': 'call-1',
                }
            )
        self.usage = {
            'prompt_tokens': 10,
            'completion_tokens': 5,
            'total_tokens': 15,
        }


@pytest.fixture
def config_openai_responses():
    # Reasoning-capable model, with Responses flag enabled
    return LLMConfig(model='gpt-5', api_key='test', use_openai_responses=True)


@patch('openhands.llm.llm.litellm.supports_reasoning', return_value=True)
@patch('openhands.llm.llm.litellm_responses')
def test_responses_success_normalizes(
    mock_responses, _supports, config_openai_responses
):
    mock_responses.return_value = DummyResponses(with_tool=True)
    llm = LLM(config_openai_responses)

    resp = llm.completion(messages=[{'role': 'user', 'content': 'Hi'}])
    # Pass api_key=None to avoid triggering OpenAI client in fallback path

    # Should return a chat-completions shaped response
    assert resp.get('id') == 'resp-123'
    assert resp.get('model') == 'gpt-5'
    assert resp.get('usage').get('prompt_tokens') == 10
    # Check message content and reasoning
    msg = resp.choices[0].message
    assert msg.content == 'Final answer'
    assert getattr(msg, 'reasoning_content', None) == 'I will think step by step.'
    # Tool calls synthesized
    assert msg.tool_calls is not None
    assert msg.tool_calls[0]['type'] == 'function'
    assert msg.tool_calls[0]['function']['name'] == 'do_something'


@patch('openhands.llm.llm.litellm.supports_reasoning', return_value=True)
@patch('openhands.llm.llm.litellm_completion')
@patch(
    'openhands.llm.llm.LLM._normalize_openai_responses_to_chat_completion',
    side_effect=RuntimeError('normalize failed'),
)
@patch('openhands.llm.llm.litellm_responses')
def test_responses_fallback_to_chat_completions(
    mock_resp, _normalize, mock_completion, _supports, config_openai_responses
):
    # Force responses to return a dummy object, but normalization fails -> fallback
    mock_resp.return_value = DummyResponses()
    # Fallback completion returns a minimal valid structure
    mock_completion.return_value = {
        'id': 'cc-1',
        'model': 'gpt-5',
        'choices': [{'message': {'role': 'assistant', 'content': 'ok'}}],
        'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2},
    }

    llm = LLM(config_openai_responses)
    resp = llm.completion(messages=[{'role': 'user', 'content': 'Hi'}])

    assert resp.get('id') == 'cc-1'
    assert resp.get('choices')[0]['message']['content'] == 'ok'


@patch('openhands.llm.llm.litellm_completion')
@patch('openhands.llm.llm.litellm.supports_reasoning', return_value=True)
def test_flag_disabled_uses_chat_completions(_supports, mock_completion):
    mock_completion.return_value = {
        'id': 'cc-2',
        'model': 'gpt-5',
        'choices': [{'message': {'role': 'assistant', 'content': 'ok2'}}],
        'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2},
    }
    cfg = LLMConfig(model='gpt-5', api_key='test', use_openai_responses=False)
    llm = LLM(cfg)
    resp = llm.completion(messages=[{'role': 'user', 'content': 'Hi'}])
    assert resp.get('id') == 'cc-2'
