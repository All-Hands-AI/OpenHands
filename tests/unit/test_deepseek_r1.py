"""
Unit tests for DeepSeek R1 integration.
"""

from unittest.mock import Mock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.llm.deepseek_r1 import (
    DeepSeekR1Config,
    DeepSeekR1Optimizer,
    create_deepseek_r1_llm,
    estimate_deepseek_r1_cost,
    is_deepseek_r1_model,
)


class TestDeepSeekR1Config:
    """Test DeepSeek R1 configuration."""

    def test_get_optimized_config_default(self):
        """Test getting optimized config with defaults."""
        config = DeepSeekR1Config.get_optimized_config()

        assert config.model == 'deepseek-r1-0528'
        assert config.base_url == 'https://api.deepseek.com'
        assert config.temperature == 0.0
        assert config.max_output_tokens == 4096
        assert config.top_p == 0.95
        assert config.timeout == 60

    def test_get_optimized_config_with_params(self):
        """Test getting optimized config with custom parameters."""
        config = DeepSeekR1Config.get_optimized_config(
            api_key='test-key',
            base_url='https://custom.api.com',
            temperature=0.5,
            max_output_tokens=2048,
        )

        assert config.api_key.get_secret_value() == 'test-key'
        assert config.base_url == 'https://custom.api.com'
        assert config.temperature == 0.5
        assert config.max_output_tokens == 2048

    @patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'env-key'})
    def test_get_optimized_config_from_env(self):
        """Test getting API key from environment."""
        config = DeepSeekR1Config.get_optimized_config()

        assert config.api_key.get_secret_value() == 'env-key'


class TestDeepSeekR1Optimizer:
    """Test DeepSeek R1 optimizer."""

    def setup_method(self):
        """Setup test fixtures."""
        config = LLMConfig(model='deepseek-r1-0528')
        self.optimizer = DeepSeekR1Optimizer(config)

    def test_is_complex_task(self):
        """Test complex task detection."""
        assert self.optimizer._is_complex_task('Please analyze this code')
        assert self.optimizer._is_complex_task('Debug the following issue')
        assert self.optimizer._is_complex_task('Implement a new feature')
        assert not self.optimizer._is_complex_task('Hello world')
        assert not self.optimizer._is_complex_task('What is your name?')

    def test_add_reasoning_prompt(self):
        """Test adding reasoning prompt."""
        content = 'Fix this bug'
        result = self.optimizer._add_reasoning_prompt(content)

        assert 'step by step' in result
        assert 'reasoning process' in result
        assert content in result

    def test_optimize_messages_simple(self):
        """Test optimizing simple messages."""
        messages = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there!'},
        ]

        result = self.optimizer.optimize_messages(messages)

        # Simple messages should not be modified
        assert result == messages

    def test_optimize_messages_complex(self):
        """Test optimizing complex messages."""
        messages = [
            {'role': 'user', 'content': 'Please analyze this code and fix any bugs'},
        ]

        result = self.optimizer.optimize_messages(messages)

        # Complex messages should have reasoning prompt added
        assert len(result) == 1
        assert 'step by step' in result[0]['content']
        assert 'analyze this code' in result[0]['content']

    def test_optimize_completion_params(self):
        """Test optimizing completion parameters."""
        params = {'messages': []}

        result = self.optimizer.optimize_completion_params(params)

        assert result['temperature'] == DeepSeekR1Config.DEFAULT_TEMPERATURE
        assert result['top_p'] == DeepSeekR1Config.DEFAULT_TOP_P
        assert result['stream'] is False

    def test_optimize_completion_params_preserve_existing(self):
        """Test that existing parameters are preserved."""
        params = {
            'messages': [],
            'temperature': 0.8,
            'top_p': 0.9,
            'stream': True,
        }

        result = self.optimizer.optimize_completion_params(params)

        # Existing parameters should be preserved
        assert result['temperature'] == 0.8
        assert result['top_p'] == 0.9
        assert result['stream'] is True


class TestDeepSeekR1Utils:
    """Test DeepSeek R1 utility functions."""

    def test_is_deepseek_r1_model(self):
        """Test DeepSeek R1 model detection."""
        assert is_deepseek_r1_model('deepseek-r1-0528')
        assert is_deepseek_r1_model('deepseek-r1')
        assert is_deepseek_r1_model('deepseek/r1-0528')
        assert is_deepseek_r1_model('DEEPSEEK-R1-0528')  # Case insensitive

        assert not is_deepseek_r1_model('deepseek-chat')
        assert not is_deepseek_r1_model('gpt-4o')
        assert not is_deepseek_r1_model('claude-3-5-sonnet')

    def test_estimate_deepseek_r1_cost(self):
        """Test cost estimation."""
        cost = estimate_deepseek_r1_cost(1000, 500)

        # Expected: 1000 * 0.000014 + 500 * 0.000028 = 0.014 + 0.014 = 0.028
        expected_cost = 1000 * 0.000014 + 500 * 0.000028
        assert abs(cost - expected_cost) < 0.000001

    def test_estimate_deepseek_r1_cost_zero_tokens(self):
        """Test cost estimation with zero tokens."""
        cost = estimate_deepseek_r1_cost(0, 0)
        assert cost == 0.0

    @patch('openhands.llm.llm.LLM')
    def test_create_deepseek_r1_llm(self, mock_llm_class):
        """Test creating DeepSeek R1 LLM instance."""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm

        llm = create_deepseek_r1_llm(api_key='test-key')

        # Verify LLM was created with correct config
        mock_llm_class.assert_called_once()
        config = mock_llm_class.call_args[0][0]
        assert config.model == 'deepseek-r1-0528'
        assert config.api_key.get_secret_value() == 'test-key'

        # Verify completion method was wrapped
        assert hasattr(llm, 'completion')

    @patch('openhands.llm.llm.LLM')
    def test_create_deepseek_r1_llm_with_optimization(self, mock_llm_class):
        """Test that created LLM has optimization applied."""
        mock_llm = Mock()
        mock_completion = Mock(return_value='test response')
        mock_llm.completion = mock_completion
        mock_llm_class.return_value = mock_llm

        llm = create_deepseek_r1_llm(api_key='test-key')

        # Test that completion is optimized
        messages = [{'role': 'user', 'content': 'analyze this code'}]
        llm.completion(messages=messages)

        # Verify the completion was called (optimization applied)
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args[1]

        # Check that reasoning prompt was added
        assert 'step by step' in call_kwargs['messages'][0]['content']


if __name__ == '__main__':
    pytest.main([__file__])
