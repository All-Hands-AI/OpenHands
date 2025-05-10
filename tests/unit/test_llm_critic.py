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
            critic_api_key=SecretStr('test-critic-key'),  # Add critic API key
            critic_base_url='https://test-critic-url.com',
            critic_num_candidates=3,
            temperature=0.7,  # Add non-zero temperature for critic to work
        )

    @patch('openhands.llm.critic.LLMCritic.evaluate_candidates')
    @patch('openhands.llm.llm.litellm_completion')
    def test_llm_with_critic(self, mock_completion, mock_evaluate):
        """Test that the LLM uses the critic when enabled."""
        # Set up mocks
        # Create a mock response that mimics the structure of a ModelResponse
        mock_response = {
            'id': 'test-id',
            'choices': [{'message': {'content': 'test response', 'tool_calls': []}}],
            'model_dump': lambda: {
                'id': 'test-id',
                'choices': [
                    {'message': {'content': 'test response', 'tool_calls': []}}
                ],
            },
        }

        # Add the necessary attributes to make it work with the code
        class MockModelResponse(dict):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.choices = [
                    type(
                        'obj',
                        (object,),
                        {
                            'message': type(
                                'obj',
                                (object,),
                                {'content': 'test response', 'tool_calls': []},
                            )
                        },
                    )()
                ]

            def model_dump(self):
                return {
                    'id': 'test-id',
                    'choices': [
                        {'message': {'content': 'test response', 'tool_calls': []}}
                    ],
                }

        mock_response = MockModelResponse(mock_response)
        mock_completion.return_value = mock_response

        # Mock the evaluate_candidates method to return a list of tuples (index, LLMCriticOutput)
        # Each tuple contains the candidate index and a LLMCriticOutput object
        from openhands.llm.critic import LLMCriticOutput

        # Create a mock LLMCriticOutput with a high reward for the first candidate
        mock_critic_output = LLMCriticOutput(
            assistant_rewards=[0.8],  # High reward for the "best" response
            token_ids=[1, 2, 3],
            token_rewards=[0.1, 0.2, 0.3],
        )

        # Return a list with one tuple (0, mock_critic_output)
        # This simulates that candidate 0 is the best with a reward of 0.8
        mock_evaluate.return_value = [(0, mock_critic_output)]

        # Create LLM with critic enabled
        llm = LLM(self.config)

        # Call completion
        messages = [{'role': 'user', 'content': 'test message'}]
        response = llm.completion(messages=messages)

        # Verify that the critic was used
        self.assertGreaterEqual(
            mock_completion.call_count, 1
        )  # Called at least once for the candidate
        mock_evaluate.assert_called_once()

        # Verify that the response has a critic score
        self.assertEqual(response.critic_score, 0.8)
        self.assertEqual(response.choices[0].message.content, 'test response')

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
