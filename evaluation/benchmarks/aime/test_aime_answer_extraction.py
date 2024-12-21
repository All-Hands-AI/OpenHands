import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from evaluation.benchmarks.aime.run_infer import process_instance, parse_final_answer
from evaluation.utils.shared import EvalMetadata
from openhands.controller.state.state import State

class TestAIMEAnswerExtraction(unittest.TestCase):
    @patch('evaluation.benchmarks.aime.run_infer.create_runtime')
    @patch('evaluation.benchmarks.aime.run_infer.call_async_from_sync')
    @patch('evaluation.benchmarks.aime.run_infer.asyncio.run')
    def test_answer_extraction(self, mock_asyncio_run, mock_call_async, mock_create_runtime):
        # Create a dictionary for the instance
        mock_instance = {
            'instance_id': '2023-I-2',
            'Answer': '42',
            'Year': 2023,
            'Problem Number': 2,
            'Question': 'Test AIME question'
        }

        mock_metadata = Mock(spec=EvalMetadata)
        mock_metadata.agent_class = 'CodeActAgent'
        mock_metadata.max_iterations = 50
        mock_metadata.llm_config = {}

        mock_state = Mock(spec=State)
        mock_state.history = [
            Mock(role='human', content="User instruction with <<FINAL_ANSWER||24||FINAL_ANSWER>>"),
            Mock(role='assistant', content="Agent response"),
            Mock(role='assistant', thought="Thinking process"),
            Mock(role='assistant', content="Final answer: <<FINAL_ANSWER||42||FINAL_ANSWER>>"),
        ]
        # Set the 'thought' and 'content' attributes to be strings
        for event in mock_state.history:
            event.thought = event.thought if isinstance(event.thought, str) else ""
            event.content = event.content if isinstance(event.content, str) else ""
        mock_state.metrics = Mock()
        mock_state.metrics.get.return_value = {}
        mock_state.last_error = None
        mock_asyncio_run.return_value = mock_state

        # Mock the get_config function to return a mock config
        with patch('evaluation.benchmarks.aime.run_infer.get_config') as mock_get_config:
            mock_config = Mock()
            mock_get_config.return_value = mock_config

            # Mock the create_runtime function
            mock_create_runtime.return_value = Mock()

            # Run the process_instance function
            result = process_instance(mock_instance, mock_metadata, reset_logger=False)

        # Check if the correct answer was extracted
        self.assertTrue(result.test_result['result'])
        self.assertEqual(result.test_result['last_message'], "Final answer: <<FINAL_ANSWER||42||FINAL_ANSWER>>")
        
        # Test parse_final_answer function
        self.assertEqual(parse_final_answer("Some text <<FINAL_ANSWER||42||FINAL_ANSWER>> more text"), "42")
        self.assertEqual(parse_final_answer("No answer here"), None)

    def test_answer_extraction_from_thought(self):
        mock_instance = {
            'instance_id': '2023-I-3',
            'Answer': '11',
            'Year': 2023,
            'Problem Number': 3,
            'Question': 'Test AIME question'
        }
        mock_metadata = Mock(spec=EvalMetadata)
        mock_metadata.agent_class = 'CodeActAgent'
        mock_state = Mock(spec=State)
        mock_state.history = [
            Mock(role='assistant', thought="Thinking... <<FINAL_ANSWER||11||FINAL_ANSWER>>"),
            Mock(role='assistant', content="Final message without answer"),
        ]
        # Set the 'thought' and 'content' attributes to be strings
        for event in mock_state.history:
            event.thought = event.thought if isinstance(event.thought, str) else ""
            event.content = event.content if isinstance(event.content, str) else ""
        mock_state.metrics = Mock()
        mock_state.metrics.get.return_value = {}
        mock_state.last_error = None

        with patch('evaluation.benchmarks.aime.run_infer.asyncio.run', return_value=mock_state), \
             patch('evaluation.benchmarks.aime.run_infer.get_config'), \
             patch('evaluation.benchmarks.aime.run_infer.create_runtime'), \
             patch('evaluation.benchmarks.aime.run_infer.call_async_from_sync'):
            result = process_instance(mock_instance, mock_metadata, reset_logger=False)

        self.assertTrue(result.test_result['result'])
        self.assertEqual(result.test_result['last_message'], "Thinking... <<FINAL_ANSWER||11||FINAL_ANSWER>>")

if __name__ == '__main__':
    unittest.main()