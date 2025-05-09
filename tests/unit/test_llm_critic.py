"""Tests for the LLM critic functionality."""

import unittest
from unittest.mock import patch

from pydantic import SecretStr

from openhands.core.config import LLMConfig
from openhands.llm import LLM


class TestLLMCritic(unittest.TestCase):
    """Test the LLM critic functionality."""

    def setUp(self):
        """Set up the test."""
        self.config = LLMConfig(
            model='test-model',
            api_key=SecretStr('test-key'),
            base_url='https://test-url.com',
            use_critic=True,
            critic_model='test-critic-model',
            critic_base_url='https://test-critic-url.com',
            critic_num_candidates=3,
        )

    @patch('openhands.llm.critic.LLMCritic.evaluate_candidates')
    @patch('openhands.llm.llm.litellm_completion')
    def test_llm_with_critic(self, mock_completion, mock_evaluate):
        """Test that the LLM uses the critic when enabled."""
        # Set up mocks
        mock_completion.return_value = {
            'id': 'test-id',
            'choices': [{'message': {'content': 'test response', 'tool_calls': []}}],
        }

        mock_evaluate.return_value = (
            {
                'id': 'best-id',
                'choices': [
                    {'message': {'content': 'best response', 'tool_calls': []}}
                ],
            },
            {
                'scores': [0.5, 0.8, 0.3],
                'best_index': 1,
                'best_score': 0.8,
                'num_candidates': 3,
            },
        )

        # Create LLM with critic enabled
        llm = LLM(self.config)

        # Call completion
        messages = [{'role': 'user', 'content': 'test message'}]
        response = llm.completion(messages=messages)

        # Verify that the critic was used
        self.assertEqual(
            mock_completion.call_count, 3
        )  # Called once for each candidate
        mock_evaluate.assert_called_once()

        # Verify that the response contains critic results
        self.assertIn('critic_results', response)
        self.assertEqual(response['critic_results']['best_score'], 0.8)
        self.assertEqual(response['choices'][0]['message']['content'], 'best response')

    @patch('openhands.llm.llm.litellm_completion')
    def test_llm_without_critic(self, mock_completion):
        """Test that the LLM doesn't use the critic when disabled."""
        # Set up mock
        mock_completion.return_value = {
            'id': 'test-id',
            'choices': [{'message': {'content': 'test response', 'tool_calls': []}}],
        }

        # Create LLM with critic disabled
        config = self.config.model_copy()
        config.use_critic = False
        llm = LLM(config)

        # Call completion
        messages = [{'role': 'user', 'content': 'test message'}]
        response = llm.completion(messages=messages)

        # Verify that the critic was not used
        mock_completion.assert_called_once()
        self.assertNotIn('critic_results', response)
        self.assertEqual(response['choices'][0]['message']['content'], 'test response')


if __name__ == '__main__':
    unittest.main()
