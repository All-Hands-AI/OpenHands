"""Test to demonstrate the real-world usage of repository name triggers in microagents."""

from unittest.mock import MagicMock

import pytest

from openhands.events.action.agent import RecallAction
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource, RecallType
from openhands.events.stream import EventStream
from openhands.memory.memory import Memory
from openhands.microagent import (
    KnowledgeMicroagent,
    MicroagentMetadata,
    MicroagentType,
)


@pytest.fixture
def memory_with_repo_trigger_microagent():
    """Create a memory instance with a repository-triggered microagent."""
    # Create mock event stream
    event_stream = MagicMock(spec=EventStream)

    # Create a memory instance
    memory = Memory(event_stream=event_stream, sid='test-session')

    # Create a microagent with repo_triggers
    agent = KnowledgeMicroagent(
        name='repo_trigger_test',
        content='Test content for repo-specific microagent',
        metadata=MicroagentMetadata(
            name='repo_trigger_test',
            triggers=['test'],
            repo_triggers=['test-repo', 'another-repo'],
        ),
        source='test.md',
        type=MicroagentType.KNOWLEDGE,
    )

    # Add our test microagent to the knowledge_microagents
    memory.knowledge_microagents = {}  # Clear existing microagents
    memory.knowledge_microagents[agent.name] = agent

    # Set repository info with a matching repo name
    memory.set_repository_info('test-repo', '/workspace/test-repo')

    return memory


def test_repo_name_trigger_on_first_message(memory_with_repo_trigger_microagent):
    """Test that repository name triggers work on the first user message."""
    memory = memory_with_repo_trigger_microagent

    # Create a user message action
    message_action = MessageAction(content="Hello, I'm working on a new project")
    message_action._id = 'msg1'  # Set id using the protected attribute
    message_action._source = EventSource.USER

    # Create a recall action for workspace context
    recall_action = RecallAction(recall_type=RecallType.WORKSPACE_CONTEXT)
    recall_action._id = 'recall1'  # Set id using the protected attribute
    recall_action._source = EventSource.USER
    recall_action.query = message_action.content

    # Call the workspace context recall method directly
    recall_obs = memory._on_workspace_context_recall(recall_action)

    # Verify the observation contains the microagent knowledge
    assert recall_obs is not None
    assert len(recall_obs.microagent_knowledge) == 1
    assert recall_obs.microagent_knowledge[0].name == 'repo_trigger_test'
    assert recall_obs.microagent_knowledge[0].trigger == 'repo:test-repo'

    # Now change to a non-matching repo name
    memory.set_repository_info('non-matching-repo', '/workspace/non-matching-repo')

    # Create another recall action
    recall_action2 = RecallAction(recall_type=RecallType.WORKSPACE_CONTEXT)
    recall_action2._id = 'recall2'  # Set id using the protected attribute
    recall_action2._source = EventSource.USER
    recall_action2.query = 'Another message'

    # Call the workspace context recall method again
    recall_obs2 = memory._on_workspace_context_recall(recall_action2)

    # Verify no microagent knowledge is included
    assert recall_obs2 is not None
    assert len(recall_obs2.microagent_knowledge) == 0


def test_repo_name_trigger_on_subsequent_message(memory_with_repo_trigger_microagent):
    """Test that repository name triggers work on subsequent user messages."""
    memory = memory_with_repo_trigger_microagent

    # Create a user message action
    message_action = MessageAction(content='Can you help me with something?')
    message_action._id = 'msg1'  # Set id using the protected attribute
    message_action._source = EventSource.USER

    # Create a recall action for knowledge
    recall_action = RecallAction(recall_type=RecallType.KNOWLEDGE)
    recall_action._id = 'recall1'  # Set id using the protected attribute
    recall_action._source = EventSource.USER
    recall_action.query = message_action.content

    # Call the microagent recall method directly
    recall_obs = memory._on_microagent_recall(recall_action)

    # Verify the observation contains the microagent knowledge
    assert recall_obs is not None
    assert len(recall_obs.microagent_knowledge) == 1
    assert recall_obs.microagent_knowledge[0].name == 'repo_trigger_test'
    assert recall_obs.microagent_knowledge[0].trigger == 'repo:test-repo'

    # Now change to a non-matching repo name
    memory.set_repository_info('non-matching-repo', '/workspace/non-matching-repo')

    # Create another recall action
    recall_action2 = RecallAction(recall_type=RecallType.KNOWLEDGE)
    recall_action2._id = 'recall2'  # Set id using the protected attribute
    recall_action2._source = EventSource.USER
    recall_action2.query = 'Another question'

    # Call the microagent recall method again
    recall_obs2 = memory._on_microagent_recall(recall_action2)

    # Verify no microagent knowledge is included
    assert recall_obs2 is None


def test_repo_name_trigger_in_agent_controller(memory_with_repo_trigger_microagent):
    """Test that repository name triggers work in the agent controller flow."""
    # This test simulates the agent controller flow
    memory = memory_with_repo_trigger_microagent

    # Create a recall action for knowledge
    recall_action = RecallAction(recall_type=RecallType.KNOWLEDGE)
    recall_action._id = 'recall1'  # Set id using the protected attribute
    recall_action._source = EventSource.USER
    recall_action.query = 'Hello, can you help me with something unrelated?'

    # Call the microagent recall method directly
    recall_obs = memory._on_microagent_recall(recall_action)

    # Verify the observation contains the microagent knowledge
    assert recall_obs is not None
    assert len(recall_obs.microagent_knowledge) == 1
    assert recall_obs.microagent_knowledge[0].name == 'repo_trigger_test'
    assert recall_obs.microagent_knowledge[0].trigger == 'repo:test-repo'

    # Now change to a non-matching repo name
    memory.set_repository_info('non-matching-repo', '/workspace/non-matching-repo')

    # Create another recall action
    recall_action2 = RecallAction(recall_type=RecallType.KNOWLEDGE)
    recall_action2._id = 'recall2'  # Set id using the protected attribute
    recall_action2._source = EventSource.USER
    recall_action2.query = 'Another unrelated message'

    # This should not trigger the microagent
    recall_obs2 = memory._on_microagent_recall(recall_action2)

    # If the repo name trigger is working correctly, this should be None
    # because no microagent was triggered
    assert recall_obs2 is None
