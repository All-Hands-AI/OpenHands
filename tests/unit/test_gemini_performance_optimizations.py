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
        config = LLMConfig(
            model='gemini-2.5-pro',
            api_key='test_key'
        )
        # reasoning_effort should remain None for Gemini models
        assert config.reasoning_effort is None

    def test_gemini_variant_model_keeps_none_reasoning_effort(self):
        """Test that Gemini model variants keep reasoning_effort=None."""
        config = LLMConfig(
            model='google/gemini-2.5-pro-latest',
            api_key='test_key'
        )
        # reasoning_effort should remain None for Gemini model variants
        assert config.reasoning_effort is None

    def test_non_gemini_model_gets_high_reasoning_effort(self):
        """Test that non-Gemini models get reasoning_effort='high' by default."""
        config = LLMConfig(
            model='gpt-4o',
            api_key='test_key'
        )
        # Non-Gemini models should get reasoning_effort='high'
        assert config.reasoning_effort == 'high'

    def test_o1_model_gets_high_reasoning_effort(self):
        """Test that o1 models get reasoning_effort='high' by default."""
        config = LLMConfig(
            model='o1-preview',
            api_key='test_key'
        )
        # o1 models should get reasoning_effort='high'
        assert config.reasoning_effort == 'high'

    def test_explicit_reasoning_effort_preserved(self):
        """Test that explicitly set reasoning_effort is preserved."""
        config = LLMConfig(
            model='gemini-2.5-pro',
            api_key='test_key',
            reasoning_effort='medium'
        )
        # Explicitly set reasoning_effort should be preserved
        assert config.reasoning_effort == 'medium'

    def test_claude_model_gets_high_reasoning_effort(self):
        """Test that Claude models get reasoning_effort='high' by default."""
        config = LLMConfig(
            model='anthropic/claude-3-5-sonnet-20241022',
            api_key='test_key'
        )
        # Claude models should get reasoning_effort='high'
        assert config.reasoning_effort == 'high'


class TestLLMGeminiThinkingBudgetOptimization:
    """Test LLM class Gemini thinking budget optimization logic."""

    @pytest.fixture
    def gemini_config(self):
        """Fixture for Gemini LLM configuration."""
        return LLMConfig(
            model='gemini-2.5-pro',
            api_key='test_key',
            reasoning_effort=None
        )

    @pytest.fixture
    def gemini_variant_config(self):
        """Fixture for Gemini variant LLM configuration."""
        return LLMConfig(
            model='google/gemini-2.5-pro',
            api_key='test_key',
            reasoning_effort=None
        )

    @pytest.fixture
    def non_gemini_config(self):
        """Fixture for non-Gemini LLM configuration."""
        return LLMConfig(
            model='o1',
            api_key='test_key',
            reasoning_effort='high'
        )

    @pytest.fixture
    def sample_messages(self):
        """Fixture for sample messages."""
        return [
            {'role': 'user', 'content': 'Hello, how are you?'}
        ]

    @patch('openhands.llm.llm.litellm_completion')
    def test_gemini_none_reasoning_effort_uses_thinking_budget(
        self, mock_completion, gemini_config, sample_messages
    ):
        """Test that Gemini with reasoning_effort=None uses thinking budget."""
        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5}
        }

        llm = LLM(gemini_config)
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
            model='gemini-2.5-pro',
            api_key='test_key',
            reasoning_effort='low'
        )

        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5}
        }

        llm = LLM(config)
        llm.completion(messages=sample_messages)

        # Verify that thinking budget was set and reasoning_effort was None
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' in call_kwargs
        assert call_kwargs['thinking'] == {'budget_tokens': 128}
        assert call_kwargs.get('reasoning_effort') is None

    @patch('openhands.llm.llm.litellm_completion')
    def test_gemini_none_string_reasoning_effort_uses_thinking_budget(
        self, mock_completion, sample_messages
    ):
        """Test that Gemini with reasoning_effort='none' uses thinking budget."""
        config = LLMConfig(
            model='gemini-2.5-pro',
            api_key='test_key',
            reasoning_effort='none'
        )

        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5}
        }

        llm = LLM(config)
        llm.completion(messages=sample_messages)

        # Verify that thinking budget was set and reasoning_effort was None
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' in call_kwargs
        assert call_kwargs['thinking'] == {'budget_tokens': 128}
        assert call_kwargs.get('reasoning_effort') is None

    @patch('openhands.llm.llm.litellm_completion')
    def test_gemini_medium_reasoning_effort_uses_thinking_budget_fixme(
        self, mock_completion, sample_messages
    ):
        """Test that Gemini with reasoning_effort='medium' uses thinking budget (FIXME behavior)."""
        config = LLMConfig(
            model='gemini-2.5-pro',
            api_key='test_key',
            reasoning_effort='medium'
        )

        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5}
        }

        llm = LLM(config)
        llm.completion(messages=sample_messages)

        # Verify that thinking budget was set (FIXME: should pass through reasoning_effort)
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' in call_kwargs
        assert call_kwargs['thinking'] == {'budget_tokens': 128}
        assert call_kwargs.get('reasoning_effort') is None

    @patch('openhands.llm.llm.litellm_completion')
    def test_gemini_high_reasoning_effort_uses_thinking_budget_fixme(
        self, mock_completion, sample_messages
    ):
        """Test that Gemini with reasoning_effort='high' uses thinking budget (FIXME behavior)."""
        config = LLMConfig(
            model='gemini-2.5-pro',
            api_key='test_key',
            reasoning_effort='high'
        )

        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5}
        }

        llm = LLM(config)
        llm.completion(messages=sample_messages)

        # Verify that thinking budget was set (FIXME: should pass through reasoning_effort)
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' in call_kwargs
        assert call_kwargs['thinking'] == {'budget_tokens': 128}
        assert call_kwargs.get('reasoning_effort') is None

    @patch('openhands.llm.llm.litellm_completion')
    def test_gemini_variant_uses_thinking_budget(
        self, mock_completion, gemini_variant_config, sample_messages
    ):
        """Test that Gemini model variants use thinking budget optimization."""
        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5}
        }

        llm = LLM(gemini_variant_config)
        llm.completion(messages=sample_messages)

        # Verify that thinking budget was set and reasoning_effort was None
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' in call_kwargs
        assert call_kwargs['thinking'] == {'budget_tokens': 128}
        assert call_kwargs.get('reasoning_effort') is None

    @patch('openhands.llm.llm.litellm_completion')
    def test_non_gemini_uses_reasoning_effort(
        self, mock_completion, non_gemini_config, sample_messages
    ):
        """Test that non-Gemini models use reasoning_effort instead of thinking budget."""
        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5}
        }

        llm = LLM(non_gemini_config)
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
            api_key='test_key'
        )

        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5}
        }

        llm = LLM(config)
        llm.completion(messages=sample_messages)

        # Verify that neither thinking budget nor reasoning_effort were set
        call_kwargs = mock_completion.call_args[1]
        assert 'thinking' not in call_kwargs
        assert 'reasoning_effort' not in call_kwargs

    @patch('openhands.llm.llm.litellm_completion')
    def test_thinking_budget_token_count(self, mock_completion, gemini_config):
        """Test that the thinking budget uses exactly 128 tokens."""
        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5}
        }

        llm = LLM(gemini_config)
        sample_messages = [
            {'role': 'user', 'content': 'Test message'}
        ]
        llm.completion(messages=sample_messages)

        # Verify the exact thinking budget configuration
        call_kwargs = mock_completion.call_args[1]
        thinking_config = call_kwargs.get('thinking')
        assert thinking_config is not None
        assert thinking_config['budget_tokens'] == 128


class TestGeminiPerformanceIntegration:
    """Integration tests for Gemini performance optimizations."""

    def test_gemini_config_and_llm_integration(self):
        """Test that LLMConfig and LLM work together correctly for Gemini."""
        # Create Gemini config (should have reasoning_effort=None)
        config = LLMConfig(
            model='gemini-2.5-pro',
            api_key='test_key'
        )
        assert config.reasoning_effort is None

        # Create LLM with Gemini config
        llm = LLM(config)
        assert llm.config.reasoning_effort is None
        assert 'gemini-2.5-pro' in llm.config.model

    def test_non_gemini_config_and_llm_integration(self):
        """Test that LLMConfig and LLM work together correctly for non-Gemini."""
        # Create non-Gemini config (should have reasoning_effort='high')
        config = LLMConfig(
            model='gpt-4o',
            api_key='test_key'
        )
        assert config.reasoning_effort == 'high'

        # Create LLM with non-Gemini config
        llm = LLM(config)
        assert llm.config.reasoning_effort == 'high'
        assert 'gemini' not in llm.config.model.lower()

    @patch('openhands.llm.llm.litellm_completion')
    def test_performance_optimization_end_to_end(self, mock_completion):
        """Test the complete performance optimization flow end-to-end."""
        # Mock the completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Optimized response'}}],
            'usage': {'prompt_tokens': 50, 'completion_tokens': 25}
        }

        # Create Gemini configuration
        config = LLMConfig(
            model='gemini-2.5-pro',
            api_key='test_key'
        )

        # Verify config has optimized defaults
        assert config.reasoning_effort is None

        # Create LLM and make completion
        llm = LLM(config)
        messages = [
            {'role': 'user', 'content': 'Solve this complex problem'}
        ]
        
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