import unittest
from unittest.mock import MagicMock, patch

from openhands.core import Conversation, OpenHands
from openhands.core.config.openhands_config import OpenHandsConfig


class TestConversation(unittest.TestCase):
    def test_conversation_dataclass(self):
        """Test that the Conversation class is a dataclass with the expected fields."""
        # Create mock objects for the constructor
        conversation_id = 'test-conversation-id'
        runtime = MagicMock()
        llm = MagicMock()
        event_stream = MagicMock()
        agent_controller = MagicMock()

        # Create a Conversation instance
        conversation = Conversation(
            conversation_id=conversation_id,
            runtime=runtime,
            llm=llm,
            event_stream=event_stream,
            agent_controller=agent_controller,
        )

        # Verify that the fields are set correctly
        self.assertEqual(conversation.conversation_id, conversation_id)
        self.assertEqual(conversation.runtime, runtime)
        self.assertEqual(conversation.llm, llm)
        self.assertEqual(conversation.event_stream, event_stream)
        self.assertEqual(conversation.agent_controller, agent_controller)


class TestOpenHands(unittest.TestCase):
    @patch('openhands.core.openhands.create_runtime')
    @patch('openhands.core.openhands.EventStream')
    @patch('openhands.core.openhands.LLM')
    @patch('openhands.core.openhands.Agent')
    @patch('openhands.core.openhands.AgentController')
    def test_create_conversation(
        self,
        mock_agent_controller,
        mock_agent,
        mock_llm,
        mock_event_stream,
        mock_create_runtime,
    ):
        """Test that the create_conversation method creates all the expected components."""
        # Create mock objects
        config = OpenHandsConfig()
        mock_runtime = MagicMock()
        mock_create_runtime.return_value = mock_runtime

        mock_event_stream_instance = MagicMock()
        mock_event_stream_instance.sid = 'generated-id'
        mock_event_stream.return_value = mock_event_stream_instance

        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        mock_agent_instance = MagicMock()
        mock_agent.return_value = mock_agent_instance

        mock_agent_controller_instance = MagicMock()
        mock_agent_controller.return_value = mock_agent_controller_instance

        # Create an OpenHands instance and call create_conversation
        openhands = OpenHands(config)
        conversation = openhands.create_conversation()

        # Verify that all the expected methods were called
        mock_create_runtime.assert_called_with(config)
        mock_event_stream.assert_called_once()
        mock_llm.assert_called_once()
        mock_agent.assert_called_once()
        mock_agent_controller.assert_called_once()

        # Verify that the returned Conversation has the expected attributes
        self.assertEqual(conversation.conversation_id, 'generated-id')
        self.assertEqual(conversation.runtime, mock_runtime)
        self.assertEqual(conversation.llm, mock_llm_instance)
        self.assertEqual(conversation.event_stream, mock_event_stream_instance)
        self.assertEqual(conversation.agent_controller, mock_agent_controller_instance)

    @patch('openhands.core.openhands.create_runtime')
    @patch('openhands.core.openhands.EventStream')
    @patch('openhands.core.openhands.LLM')
    @patch('openhands.core.openhands.Agent')
    @patch('openhands.core.openhands.AgentController')
    def test_create_conversation_with_id(
        self,
        mock_agent_controller,
        mock_agent,
        mock_llm,
        mock_event_stream,
        mock_create_runtime,
    ):
        """Test that the create_conversation method uses the provided conversation_id."""
        # Create mock objects
        config = OpenHandsConfig()
        conversation_id = 'custom-conversation-id'

        mock_runtime = MagicMock()
        mock_create_runtime.return_value = mock_runtime

        mock_event_stream_instance = MagicMock()
        mock_event_stream.return_value = mock_event_stream_instance

        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        mock_agent_instance = MagicMock()
        mock_agent.return_value = mock_agent_instance

        mock_agent_controller_instance = MagicMock()
        mock_agent_controller.return_value = mock_agent_controller_instance

        # Create an OpenHands instance and call create_conversation with a custom ID
        openhands = OpenHands(config)
        conversation = openhands.create_conversation(conversation_id=conversation_id)

        # Verify that the EventStream and AgentController were created with the custom ID
        mock_event_stream.assert_called_once_with(sid=conversation_id)
        mock_agent_controller.assert_called_once_with(
            agent=mock_agent_instance,
            event_stream=mock_event_stream_instance,
            max_iterations=config.max_iterations,
            max_budget_per_task=config.max_budget_per_task,
            agent_to_llm_config=config.get_agent_to_llm_config_map(),
            agent_configs=config.get_agent_configs(),
            sid=conversation_id,
        )

        # Verify that the returned Conversation has the custom ID
        self.assertEqual(conversation.conversation_id, conversation_id)


if __name__ == '__main__':
    unittest.main()
