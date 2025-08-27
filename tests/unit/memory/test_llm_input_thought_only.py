import os
import sys
from unittest.mock import MagicMock

from openhands.core.config.agent_config import AgentConfig

# Ensure this repo takes precedence over any installed openhands package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from openhands.events.action import Thought
from openhands.events.action.agent import AgentFinishAction
from openhands.events.action.message import MessageAction
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


def test_llm_receives_only_thought_text():
    # Setup
    agent_config = AgentConfig()
    prompt_manager = MagicMock(spec=PromptManager)
    prompt_manager.get_system_message.return_value = 'System message'
    cm = ConversationMemory(agent_config, prompt_manager)

    user_msg = MessageAction(content='hi')
    finish = AgentFinishAction(
        final_thought='done',
        thought=Thought(text='visible', reasoning_content='secret'),
    )

    messages = cm.process_events(
        condensed_history=[finish],
        initial_user_action=user_msg,
        max_message_chars=None,
        vision_is_active=False,
    )

    # Find the assistant message produced from AgentFinishAction
    assistant_texts = []
    for m in messages:
        if m.role == 'assistant':
            for c in m.content:
                if hasattr(c, 'text'):
                    assistant_texts.append(c.text)
    combined = '\n'.join(assistant_texts)
    assert 'visible' in combined
    assert 'secret' not in combined
