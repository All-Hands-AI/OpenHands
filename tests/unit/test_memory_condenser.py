import pytest
from unittest.mock import MagicMock, patch

def test_memory_condenser_with_mocked_litellm():
    with patch('opendevin.llm.llm.litellm') as mock_litellm:
        mock_litellm.completion.return_value = {'choices': [{'message': {'content': 'Mocked completion response'}}]}
        mock_litellm.completion_cost.return_value = 0.0
        mock_litellm.get_model_info.return_value = {'max_input_tokens': 4096, 'max_output_tokens': 1024}

        from opendevin.llm.llm import LLM  # Import LLM here, after litellm has been mocked

        llm = LLM(model='test-model', api_key='test-key')
        response = llm.completion(messages=[{'content': 'Test message'}])
        assert response == {'choices': [{'message': {'content': 'Mocked completion response'}}]}, 'The completion response did not match the expected mock response'


@pytest.fixture
def llm_mock():
    llm = MagicMock(spec=LLM)
    llm.get_token_count = MagicMock(side_effect=[20000, 10000])  # First call exceeds limit, second does not
    return llm

@pytest.fixture
def prompts_mock():
    action_prompt = MagicMock(return_value='Action prompt based on events')
    summarize_prompt = MagicMock(return_value='Summarize prompt based on events')
    return action_prompt, summarize_prompt

def test_condensation_needed(llm_mock, prompts_mock):
    action_prompt, summarize_prompt = prompts_mock
    condenser = MemoryCondenser(action_prompt=action_prompt, summarize_prompt=summarize_prompt)
    core_events = [{'content': 'Core event'}]
    recent_events = [{'content': 'Recent event'}]

    condensed_output, did_condense = condenser.condense(llm_mock, core_events, recent_events)
    assert did_condense
    assert 'Summarize prompt based on events' in condensed_output

def test_no_condensation_needed(llm_mock, prompts_mock):
    action_prompt, summarize_prompt = prompts_mock
    condenser = MemoryCondenser(action_prompt=action_prompt, summarize_prompt=summarize_prompt)
    core_events = [{'content': 'Core event'}]
    recent_events = [{'content': 'Recent event'}]

    llm_mock.get_token_count.return_value = 500  # Token count well below the limit
    condensed_output, did_condense = condenser.condense(llm_mock, core_events, recent_events)
    assert not did_condense
    assert 'Action prompt based on events' in condensed_output

def test_core_events_unchanged(llm_mock, prompts_mock):
    action_prompt, summarize_prompt = prompts_mock
    condenser = MemoryCondenser(action_prompt=action_prompt, summarize_prompt=summarize_prompt)
    core_events = [{'content': 'Core event'}]
    recent_events = [{'content': 'Recent event'}]

    _, _ = condenser.condense(llm_mock, core_events, recent_events)
    assert core_events == [{'content': 'Core event'}]  # Core events should remain unchanged

