"""Test to demonstrate the integration of repository name triggers in microagents."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from openhands.events.action.agent import RecallAction
from openhands.events.event import EventSource, RecallType
from openhands.events.stream import EventStream
from openhands.memory.memory import Memory
from openhands.microagent import (
    KnowledgeMicroagent,
    MicroagentMetadata,
    MicroagentType,
)


@pytest.fixture
def temp_microagents_dir_with_repo_triggers():
    """Create a temporary directory with test microagents including repo triggers."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        # Create test knowledge agent with repo triggers
        knowledge_agent = """---
# type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - test
  - pytest
repo_triggers:
  - test-repo
  - another-repo
---

# Test Guidelines with Repo Triggers

Testing best practices and guidelines for specific repositories.
"""
        (root / 'knowledge.md').write_text(knowledge_agent)

        yield root


def test_repo_name_trigger_integration(temp_microagents_dir_with_repo_triggers):
    """Test the integration of repository name triggers in a simulated application flow."""
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

    # Create a recall action with an unrelated query
    recall_action = RecallAction(recall_type=RecallType.KNOWLEDGE)
    recall_action._id = 'msg1'  # Set id using the protected attribute
    recall_action._source = EventSource.USER
    recall_action.query = 'Hello, can you help me with something unrelated?'

    # Call the microagent recall method directly
    # This should trigger the microagent because of the repo name
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
    recall_action2._id = 'msg2'  # Set id using the protected attribute
    recall_action2._source = EventSource.USER
    recall_action2.query = 'Another unrelated message'

    # This should not trigger the microagent
    recall_obs2 = memory._on_microagent_recall(recall_action2)

    # If the repo name trigger is working correctly, this should be None
    # because no microagent was triggered
    assert recall_obs2 is None
