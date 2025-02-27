import os
import shutil
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.message import Message, TextContent
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource
from openhands.events.stream import EventStream
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


@pytest.fixture
def prompt_dir(tmp_path):
    # Copy contents from "openhands/agenthub/codeact_agent" to the temp directory
    shutil.copytree(
        'openhands/agenthub/codeact_agent/prompts', tmp_path, dirs_exist_ok=True
    )
    return tmp_path


@pytest.fixture
def microagent_dir(tmp_path):
    # Create a temporary directory for microagents
    microagent_dir = tmp_path / "microagents"
    microagent_dir.mkdir()
    
    # Create a test knowledge microagent
    knowledge_microagent = """
---
name: Test Knowledge Microagent
type: knowledge
agent: CodeActAgent
triggers:
- test_keyword
---

This is test knowledge microagent content.
"""
    
    # Create a test repo microagent
    repo_microagent = """
---
name: Test Repo Microagent
type: repo
agent: CodeActAgent
---

This is test repo microagent content.
"""
    
    with open(microagent_dir / "knowledge_microagent.md", "w") as f:
        f.write(knowledge_microagent)
    
    with open(microagent_dir / "repo_microagent.md", "w") as f:
        f.write(repo_microagent)
    
    return str(microagent_dir)


def test_conversation_memory_initialization(microagent_dir):
    event_stream = EventStream()
    memory = ConversationMemory(
        event_stream=event_stream,
        microagents_dir=microagent_dir,
    )
    
    # Check that microagents were loaded
    assert len(memory.knowledge_microagents) == 1
    assert len(memory.repo_microagents) == 1
    assert "Test Knowledge Microagent" in memory.knowledge_microagents
    assert "Test Repo Microagent" in memory.repo_microagents


def test_conversation_memory_first_user_message(microagent_dir, prompt_dir):
    event_stream = EventStream()
    memory = ConversationMemory(
        event_stream=event_stream,
        microagents_dir=microagent_dir,
    )
    
    # Create a prompt manager and set it in the memory
    prompt_manager = PromptManager(prompt_dir=prompt_dir)
    memory.set_prompt_manager(prompt_manager)
    
    # Set repository info
    memory.set_repository_info("test/repo", "/workspace/test")
    
    # Create a mock for add_info_to_initial_message
    with patch.object(prompt_manager, 'add_info_to_initial_message') as mock_add_info:
        # Create a user message
        user_message = MessageAction(content="Hello", source="user")
        
        # Process the first user message
        memory.on_event(user_message)
        
        # Check that add_info_to_initial_message was called
        mock_add_info.assert_called_once()


def test_conversation_memory_enhance_message(microagent_dir, prompt_dir):
    event_stream = EventStream()
    memory = ConversationMemory(
        event_stream=event_stream,
        microagents_dir=microagent_dir,
    )
    
    # Create a prompt manager and set it in the memory
    prompt_manager = PromptManager(prompt_dir=prompt_dir)
    memory.set_prompt_manager(prompt_manager)
    
    # Create a user message with the trigger keyword
    user_message = MessageAction(content="This contains test_keyword in it", source="user")
    
    # Process the user message
    memory.on_event(user_message)
    
    # Check that the message was enhanced
    assert "extra_info" in user_message.content
    assert "test knowledge microagent content" in user_message.content.lower()


def test_conversation_memory_load_user_workspace_microagents(microagent_dir):
    event_stream = EventStream()
    memory = ConversationMemory(
        event_stream=event_stream,
        microagents_dir=microagent_dir,
    )
    
    # Create mock microagents
    knowledge_microagent = MagicMock()
    knowledge_microagent.name = "User Knowledge Microagent"
    knowledge_microagent.__class__.__name__ = "KnowledgeMicroAgent"
    
    repo_microagent = MagicMock()
    repo_microagent.name = "User Repo Microagent"
    repo_microagent.__class__.__name__ = "RepoMicroAgent"
    
    # Load the microagents
    memory.load_user_workspace_microagents([knowledge_microagent, repo_microagent])
    
    # Check that the microagents were loaded
    assert "User Knowledge Microagent" in memory.knowledge_microagents
    assert "User Repo Microagent" in memory.repo_microagents