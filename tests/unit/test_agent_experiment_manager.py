import os
import unittest
from unittest.mock import patch

from openhands.core.config import AgentConfig
from openhands.experiments.agent_experiment_manager import AgentExperimentManager
from openhands.server.session.conversation_init_data import ConversationInitData


class TestAgentExperimentManager(unittest.TestCase):
    def setUp(self):
        # Save original environment variables
        self.original_env = os.environ.copy()

    def tearDown(self):
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_no_custom_system_prompt(self):
        """Test that the experiment manager returns unmodified settings when no custom prompt is set."""
        # Create conversation settings
        conversation_settings = ConversationInitData()

        # Run the experiment manager
        modified_settings = AgentExperimentManager.run_conversation_variant_test(
            'test_user', 'test_conversation', conversation_settings
        )

        # Verify that the settings are unchanged
        self.assertEqual(modified_settings, conversation_settings)
        self.assertIsNone(modified_settings.agent_config)

    def test_custom_system_prompt_from_env(self):
        """Test that the experiment manager applies a custom system prompt from environment variables."""
        # Set environment variable for custom system prompt
        os.environ['OPENHANDS_SYSTEM_PROMPT_FILENAME'] = 'custom_prompt.j2'

        # Create conversation settings
        conversation_settings = ConversationInitData()

        # Run the experiment manager
        modified_settings = AgentExperimentManager.run_conversation_variant_test(
            'test_user', 'test_conversation', conversation_settings
        )

        # Verify that the settings have been modified
        self.assertIsNotNone(modified_settings.agent_config)
        self.assertEqual(
            modified_settings.agent_config.system_prompt_filename, 'custom_prompt.j2'
        )

    def test_custom_system_prompt_with_existing_agent_config(self):
        """Test that the experiment manager modifies an existing agent config."""
        # Set environment variable for custom system prompt
        os.environ['OPENHANDS_SYSTEM_PROMPT_FILENAME'] = 'custom_prompt.j2'

        # Create conversation settings with an existing agent config
        agent_config = AgentConfig(system_prompt_filename='original_prompt.j2')
        conversation_settings = ConversationInitData(agent_config=agent_config)

        # Run the experiment manager
        modified_settings = AgentExperimentManager.run_conversation_variant_test(
            'test_user', 'test_conversation', conversation_settings
        )

        # Verify that the settings have been modified
        self.assertIsNotNone(modified_settings.agent_config)
        self.assertEqual(
            modified_settings.agent_config.system_prompt_filename, 'custom_prompt.j2'
        )

    @patch('openhands.experiments.agent_experiment_manager.logger')
    def test_logging(self, mock_logger):
        """Test that the experiment manager logs correctly."""
        # Set environment variable for custom system prompt
        os.environ['OPENHANDS_SYSTEM_PROMPT_FILENAME'] = 'custom_prompt.j2'

        # Create conversation settings
        conversation_settings = ConversationInitData()

        # Run the experiment manager
        AgentExperimentManager.run_conversation_variant_test(
            'test_user', 'test_conversation', conversation_settings
        )

        # Verify that the logger was called with the expected message
        mock_logger.info.assert_called_with(
            'Using custom system prompt from environment: custom_prompt.j2',
            extra={
                'user_id': 'test_user',
                'conversation_id': 'test_conversation',
                'experiment': 'custom_system_prompt',
            },
        )
