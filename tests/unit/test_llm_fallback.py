import pytest
from unittest.mock import patch, MagicMock

from litellm.exceptions import RateLimitError
from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM


def test_llm_fallback_init():
    # Test that fallback LLMs are properly initialized
    primary_config = LLMConfig(model='model1')
    fallback1 = LLMConfig(model='model2')
    fallback2 = LLMConfig(model='model3')
    primary_config.fallback_llms = [fallback1, fallback2]

    llm = LLM(primary_config)
    assert llm.get_current_model() == 'model1'
    assert len(llm._fallback_llms) == 2
    assert llm._fallback_llms[0].config.model == 'model2'
    assert llm._fallback_llms[1].config.model == 'model3'


def test_llm_fallback_on_rate_limit():
    # Test that LLM switches to fallback on rate limit error
    primary_config = LLMConfig(model='model1')
    fallback1 = LLMConfig(model='model2')
    primary_config.fallback_llms = [fallback1]

    llm = LLM(primary_config)
    
    # Mock the completion functions
    primary_error = RateLimitError('Please try again in 60.5s')
    llm._completion_unwrapped = MagicMock(side_effect=primary_error)
    llm._fallback_llms[0]._completion_unwrapped = MagicMock(return_value={'choices': [{'message': {'content': 'success'}}]})

    # Call completion and verify fallback is used
    result = llm.completion(messages=[{'role': 'user', 'content': 'test'}])
    assert result['choices'][0]['message']['content'] == 'success'
    assert llm.get_current_model() == 'model2'


def test_llm_fallback_reset():
    # Test that LLM resets to primary after rate limit expires
    primary_config = LLMConfig(model='model1')
    fallback1 = LLMConfig(model='model2')
    primary_config.fallback_llms = [fallback1]

    llm = LLM(primary_config)
    llm._current_llm_index = 1  # Simulate using fallback
    
    # Reset and verify
    llm.reset_fallback_index()
    assert llm.get_current_model() == 'model1'


def test_llm_no_more_fallbacks():
    # Test that error is re-raised when no more fallbacks are available
    primary_config = LLMConfig(model='model1')
    fallback1 = LLMConfig(model='model2')
    primary_config.fallback_llms = [fallback1]

    llm = LLM(primary_config)
    
    # Mock both LLMs to fail
    error = RateLimitError('Rate limit exceeded')
    llm._completion_unwrapped = MagicMock(side_effect=error)
    llm._fallback_llms[0]._completion_unwrapped = MagicMock(side_effect=error)

    # Verify error is raised when no more fallbacks
    with pytest.raises(RateLimitError):
        llm.completion(messages=[{'role': 'user', 'content': 'test'}])