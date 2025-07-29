"""Unit tests for Gemini 2.5 Pro performance optimizations.

Tests the reasoning_effort and thinking budget optimizations implemented
for Gemini models to achieve ~2.4x performance improvement.
"""

from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM


@pytest.fixture(autouse=True)
def mock_logger(monkeypatch):
    """Mock logger to suppress logging during tests."""
    mock_logger = MagicMock()
    monkeypatch.setattr('openhands.llm.debug_mixin.llm_prompt_logger', mock_logger)
    monkeypatch.setattr('openhands.llm.debug_mixin.llm_response_logger', mock_logger)
    monkeypatch.setattr('openhands.llm.llm.logger', mock_logger)
    monkeypatch.setattr('openhands.core.config.llm_config.logger', mock_logger)

    # Mock the log_prompt method to avoid the Message object issue
    mock_log_prompt = MagicMock()
    monkeypatch.setattr('openhands.llm.llm.LLM.log_prompt', mock_log_prompt)

    return mock_logger


class TestLLMConfigReasoningEffortDefaults:
    """Test LLMConfig reasoning_effort default behavior for different models."""

    def test_gemini_model_keeps_none_reasoning_effort(self):
        """Test that Gemini models keep reasoning_effort=None for optimization."""
        config = LLMConfig(model='gemini-2.5-pro', api_key='test_key')
        # reasoning_effort should remain None for Gemini models
        assert config.reasoning_effort is None

    def test_non_gemini_model_gets_high_reasoning_effort(self):
        """Test that non-Gemini models get reasoning_effort='high' by default."""
        config = LLMConfig(model='gpt-4o', api_key='test_key')
        # Non-Gemini models should get reasoning_effort='high'
        assert config.reasoning_effort == 'high'

    def test_explicit_reasoning_effort_preserved(self):
        """Test that explicitly set reasoning_effort is preserved."""
        config = LLMConfig(
            model='gemini-2.5-pro', api_key='test_key', reasoning_effort='medium'
        )
        # Explicitly set reasoning_effort should be preserved
        assert config.reasoning_effort == 'medium'


class TestLLMGeminiThinkingBudgetOptimization:
    """Test LLM class Gemini thinking budget optimization logic."""

    @pytest.fixture
    def sample_messages(self):
        """Fixture for sample messages."""
        return [{'role': 'user', 'content': 'Hello, how are you?'}]

    @patch('openhands.llm.llm.litellm_completion')
    def test_gemini_none_reasoning_effort_uses_thinking_budget(
        self, mock_completion, sample_messages
    ):
        """Test that Gemini with reasoning_effort=None uses thinking budget."""
        config = LLMConfig(
            model='gemini-2.5-pro', api_key='test_key', reasoning_effort=None
        )

        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5},
        }

        llm = LLM(config)
        llm.completion(messages=sample_messages)

        # Verify that thinking budget was set and reasoning_effort was None
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' in call_kwargs
        assert call_kwargs['thinking'] == {'budget_tokens': 128}
        assert call_kwargs.get('reasoning_effort') is None

    @patch('openhands.llm.llm.litellm_completion')
    def test_gemini_low_reasoning_effort_uses_thinking_budget(
        self, mock_completion, sample_messages
    ):
        """Test that Gemini with reasoning_effort='low' uses thinking budget."""
        config = LLMConfig(
            model='gemini-2.5-pro', api_key='test_key', reasoning_effort='low'
        )

        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5},
        }

        llm = LLM(config)
        llm.completion(messages=sample_messages)

        # Verify that thinking budget was set and reasoning_effort was None
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' in call_kwargs
        assert call_kwargs['thinking'] == {'budget_tokens': 128}
        assert call_kwargs.get('reasoning_effort') is None

    @patch('openhands.llm.llm.litellm_completion')
    def test_gemini_medium_reasoning_effort_passes_through(
        self, mock_completion, sample_messages
    ):
        """Test that Gemini with reasoning_effort='medium' passes through to litellm."""
        config = LLMConfig(
            model='gemini-2.5-pro', api_key='test_key', reasoning_effort='medium'
        )

        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5},
        }

        llm = LLM(config)
        llm.completion(messages=sample_messages)

        # Verify that reasoning_effort was passed through and thinking budget was not set
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' not in call_kwargs
        assert call_kwargs.get('reasoning_effort') == 'medium'

    @patch('openhands.llm.llm.litellm_completion')
    def test_gemini_high_reasoning_effort_passes_through(
        self, mock_completion, sample_messages
    ):
        """Test that Gemini with reasoning_effort='high' passes through to litellm."""
        config = LLMConfig(
            model='gemini-2.5-pro', api_key='test_key', reasoning_effort='high'
        )

        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5},
        }

        llm = LLM(config)
        llm.completion(messages=sample_messages)

        # Verify that reasoning_effort was passed through and thinking budget was not set
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' not in call_kwargs
        assert call_kwargs.get('reasoning_effort') == 'high'

    @patch('openhands.llm.llm.litellm_completion')
    def test_non_gemini_uses_reasoning_effort(self, mock_completion, sample_messages):
        """Test that non-Gemini models use reasoning_effort instead of thinking budget."""
        config = LLMConfig(model='o1', api_key='test_key', reasoning_effort='high')

        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5},
        }

        llm = LLM(config)
        llm.completion(messages=sample_messages)

        # Verify that reasoning_effort was used and thinking budget was not set
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' not in call_kwargs
        assert call_kwargs.get('reasoning_effort') == 'high'

    @patch('openhands.llm.llm.litellm_completion')
    def test_non_reasoning_model_no_optimization(
        self, mock_completion, sample_messages
    ):
        """Test that non-reasoning models don't get optimization parameters."""
        config = LLMConfig(
            model='gpt-3.5-turbo',  # Not in REASONING_EFFORT_SUPPORTED_MODELS
            api_key='test_key',
        )

        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5},
        }

        llm = LLM(config)
        llm.completion(messages=sample_messages)

        # Verify that neither thinking budget nor reasoning_effort were set
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' not in call_kwargs
        assert 'reasoning_effort' not in call_kwargs


class TestGeminiPerformanceIntegration:
    """Integration tests for Gemini performance optimizations."""

    @patch('openhands.llm.llm.litellm_completion')
    def test_performance_optimization_end_to_end(self, mock_completion):
        """Test the complete performance optimization flow end-to-end."""
        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Optimized response'}}],
            'usage': {'prompt_tokens': 50, 'completion_tokens': 25},
        }

        # Create Gemini configuration
        config = LLMConfig(model='gemini-2.5-pro', api_key='test_key')

        # Verify config has optimized defaults
        assert config.reasoning_effort is None

        # Create LLM and make completion
        llm = LLM(config)
        messages = [{'role': 'user', 'content': 'Solve this complex problem'}]

        response = llm.completion(messages=messages)

        # Verify response was generated
        assert response['choices'][0]['message']['content'] == 'Optimized response'

        # Verify optimization parameters were applied
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' in call_kwargs
        assert call_kwargs['thinking'] == {'budget_tokens': 128}
        assert call_kwargs.get('reasoning_effort') is None

        # Verify temperature and top_p were removed for reasoning models
        assert 'temperature' not in call_kwargs
        assert 'top_p' not in call_kwargs
