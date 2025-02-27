import unittest
from unittest.mock import MagicMock, patch

from openhands.controller.state.state import State
from openhands.core.message import Message, TextContent
from openhands.events.action import MessageAction
from openhands.events.observation import CmdOutputObservation
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


class TestConversationMemory(unittest.TestCase):
    def setUp(self):
        self.prompt_manager = MagicMock(spec=PromptManager)
        self.prompt_manager.get_system_message.return_value = "System message"
        self.conversation_memory = ConversationMemory(self.prompt_manager)
        self.state = MagicMock(spec=State)
        self.state.history = []

    def test_process_initial_messages(self):
        messages = self.conversation_memory.process_initial_messages(with_caching=False)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].role, "system")
        self.assertEqual(messages[0].content[0].text, "System message")
        self.assertEqual(messages[0].content[0].cache_prompt, False)

        messages = self.conversation_memory.process_initial_messages(with_caching=True)
        self.assertEqual(messages[0].content[0].cache_prompt, True)

    def test_process_events_with_message_action(self):
        user_message = MessageAction(content="Hello", source="user")
        assistant_message = MessageAction(content="Hi there", source="assistant")
        
        initial_messages = [
            Message(
                role="system",
                content=[TextContent(text="System message")]
            )
        ]
        
        messages = self.conversation_memory.process_events(
            state=self.state,
            condensed_history=[user_message, assistant_message],
            initial_messages=initial_messages,
            max_message_chars=None,
            vision_is_active=False
        )
        
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0].role, "system")
        self.assertEqual(messages[1].role, "user")
        self.assertEqual(messages[1].content[0].text, "Hello")
        self.assertEqual(messages[2].role, "assistant")
        self.assertEqual(messages[2].content[0].text, "Hi there")

    def test_process_events_with_observation(self):
        user_message = MessageAction(content="Hello", source="user")
        cmd_output = CmdOutputObservation(
            command="ls",
            exit_code=0,
            output="file1.txt\nfile2.txt",
            tool_call_metadata=None
        )
        
        initial_messages = [
            Message(
                role="system",
                content=[TextContent(text="System message")]
            )
        ]
        
        messages = self.conversation_memory.process_events(
            state=self.state,
            condensed_history=[user_message, cmd_output],
            initial_messages=initial_messages,
            max_message_chars=None,
            vision_is_active=False
        )
        
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0].role, "system")
        self.assertEqual(messages[1].role, "user")
        self.assertEqual(messages[2].role, "user")
        self.assertIn("Observed result of command executed by user", messages[2].content[0].text)
        self.assertIn("file1.txt", messages[2].content[0].text)

    def test_apply_prompt_caching(self):
        messages = [
            Message(role="system", content=[TextContent(text="System message")]),
            Message(role="user", content=[TextContent(text="User message")]),
            Message(role="assistant", content=[TextContent(text="Assistant message")]),
            Message(role="user", content=[TextContent(text="Another user message")]),
        ]
        
        self.conversation_memory.apply_prompt_caching(messages)
        
        # Only the last user message should have cache_prompt=True
        self.assertFalse(messages[0].content[0].cache_prompt)
        self.assertFalse(messages[1].content[0].cache_prompt)
        self.assertFalse(messages[2].content[0].cache_prompt)
        self.assertTrue(messages[3].content[0].cache_prompt)


if __name__ == "__main__":
    unittest.main()