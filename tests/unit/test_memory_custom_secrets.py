from unittest.mock import MagicMock

import pytest

from openhands.events.action.agent import RecallAction
from openhands.events.event import EventSource, RecallType
from openhands.events.observation.agent import RecallObservation
from openhands.events.stream import EventStream
from openhands.memory.memory import Memory
from openhands.runtime.base import Runtime


@pytest.fixture
def event_stream():
    return MagicMock(spec=EventStream)


@pytest.fixture
def memory(event_stream):
    return Memory(event_stream=event_stream, sid='test_sid')


def test_set_runtime_info_with_custom_secrets_descriptions(memory):
    """Test that set_runtime_info properly sets custom_secrets_descriptions."""
    # Create a mock runtime
    runtime = MagicMock(spec=Runtime)
    runtime.web_hosts = {'host1': 8080}
    runtime.additional_agent_instructions = 'Custom instructions'

    # Define custom secrets descriptions
    custom_secrets = {
        'API_KEY': 'Your API key for service X',
        'DB_PASSWORD': 'Database password',
    }

    # Set runtime info
    memory.set_runtime_info(runtime, custom_secrets)

    # Verify that runtime_info was set correctly
    assert memory.runtime_info is not None
    assert memory.runtime_info.available_hosts == {'host1': 8080}
    assert memory.runtime_info.additional_agent_instructions == 'Custom instructions'
    assert memory.runtime_info.custom_secrets_descriptions == custom_secrets


def test_set_runtime_info_with_empty_custom_secrets_descriptions(memory):
    """Test that set_runtime_info works with empty custom_secrets_descriptions."""
    # Create a mock runtime
    runtime = MagicMock(spec=Runtime)
    runtime.web_hosts = {'host1': 8080}
    runtime.additional_agent_instructions = 'Custom instructions'

    # Set runtime info with empty custom secrets
    memory.set_runtime_info(runtime, {})

    # Verify that runtime_info was set correctly
    assert memory.runtime_info is not None
    assert memory.runtime_info.available_hosts == {'host1': 8080}
    assert memory.runtime_info.additional_agent_instructions == 'Custom instructions'
    assert memory.runtime_info.custom_secrets_descriptions == {}


def test_workspace_context_recall_includes_custom_secrets_descriptions(
    memory, event_stream
):
    """Test that _on_workspace_context_recall includes custom_secrets_descriptions in the observation."""
    # Set up repository info
    memory.set_repository_info('test_repo', '/workspace/test_repo')

    # Set up runtime info with custom secrets
    runtime = MagicMock(spec=Runtime)
    runtime.web_hosts = {'host1': 8080}
    runtime.additional_agent_instructions = 'Custom instructions'
    custom_secrets = {'API_KEY': 'Your API key for service X'}
    memory.set_runtime_info(runtime, custom_secrets)

    # Create a recall action
    recall_action = RecallAction(
        query='test query', recall_type=RecallType.WORKSPACE_CONTEXT
    )
    recall_action._source = EventSource.USER

    # Call _on_workspace_context_recall
    observation = memory._on_workspace_context_recall(recall_action)

    # Verify that the observation includes custom_secrets_descriptions
    assert observation is not None
    assert isinstance(observation, RecallObservation)
    assert observation.custom_secrets_descriptions == custom_secrets


def test_workspace_context_recall_with_no_runtime_info(memory, event_stream):
    """Test that _on_workspace_context_recall handles the case when runtime_info is None."""
    # Set up repository info only
    memory.set_repository_info('test_repo', '/workspace/test_repo')

    # Ensure runtime_info is None
    memory.runtime_info = None

    # Create a recall action
    recall_action = RecallAction(
        query='test query', recall_type=RecallType.WORKSPACE_CONTEXT
    )
    recall_action._source = EventSource.USER

    # Call _on_workspace_context_recall
    observation = memory._on_workspace_context_recall(recall_action)

    # Verify that the observation has empty custom_secrets_descriptions
    assert observation is not None
    assert isinstance(observation, RecallObservation)
    assert observation.custom_secrets_descriptions == {}
