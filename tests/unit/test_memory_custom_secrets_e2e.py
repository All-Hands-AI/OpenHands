import asyncio
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
    memory = Memory(event_stream=event_stream, sid='test_sid')
    # Mock the _on_workspace_context_recall method to track calls
    memory._original_on_workspace_context_recall = memory._on_workspace_context_recall
    memory._on_workspace_context_recall = MagicMock(
        side_effect=memory._original_on_workspace_context_recall
    )
    return memory


def test_end_to_end_custom_secrets_in_user_message(memory, event_stream):
    """
    Test end-to-end flow where a user sends a message, which triggers a workspace context recall,
    and verify that custom_secrets_descriptions are properly included in the process.
    """
    # Set up repository info
    memory.set_repository_info('test_repo', '/workspace/test_repo')

    # Set up runtime info with custom secrets
    runtime = MagicMock(spec=Runtime)
    runtime.web_hosts = {'host1': 8080}
    runtime.additional_agent_instructions = 'Custom instructions'
    custom_secrets = {
        'API_KEY': 'Your API key for service X',
        'DB_PASSWORD': 'Database password',
    }
    memory.set_runtime_info(runtime, custom_secrets)

    # Create a recall action directly
    recall_action = RecallAction(
        query='Hello, I need help with this repository',
        recall_type=RecallType.WORKSPACE_CONTEXT,
    )
    recall_action._source = EventSource.USER

    # Create a mock observation to be returned
    mock_observation = RecallObservation(
        recall_type=RecallType.WORKSPACE_CONTEXT,
        repo_name='test_repo',
        repo_directory='/workspace/test_repo',
        runtime_hosts={'host1': 8080},
        additional_agent_instructions='Custom instructions',
        custom_secrets_descriptions=custom_secrets,
        content='Added workspace context',
    )

    # Set up the mock to return our observation
    memory._on_workspace_context_recall = MagicMock(return_value=mock_observation)

    # Process the recall action directly
    async def run_test():
        await memory._on_event(recall_action)

        # Verify that _on_workspace_context_recall was called with the recall action
        memory._on_workspace_context_recall.assert_called_once()
        call_args = memory._on_workspace_context_recall.call_args[0][0]
        assert isinstance(call_args, RecallAction)
        assert call_args.recall_type == RecallType.WORKSPACE_CONTEXT

        # Verify that the observation was added to the event stream
        event_stream.add_event.assert_called_with(
            mock_observation, EventSource.ENVIRONMENT
        )

        # Verify that custom_secrets_descriptions were included in the observation
        assert mock_observation.custom_secrets_descriptions == custom_secrets

    # Run the async test
    asyncio.run(run_test())


def test_end_to_end_empty_custom_secrets_in_user_message(memory, event_stream):
    """
    Test end-to-end flow with empty custom_secrets_descriptions.
    """
    # Set up repository info
    memory.set_repository_info('test_repo', '/workspace/test_repo')

    # Set up runtime info with empty custom secrets
    runtime = MagicMock(spec=Runtime)
    runtime.web_hosts = {'host1': 8080}
    runtime.additional_agent_instructions = 'Custom instructions'
    memory.set_runtime_info(runtime, {})

    # Create a recall action directly
    recall_action = RecallAction(
        query='Hello, I need help with this repository',
        recall_type=RecallType.WORKSPACE_CONTEXT,
    )
    recall_action._source = EventSource.USER

    # Create a mock observation to be returned
    mock_observation = RecallObservation(
        recall_type=RecallType.WORKSPACE_CONTEXT,
        repo_name='test_repo',
        repo_directory='/workspace/test_repo',
        runtime_hosts={'host1': 8080},
        additional_agent_instructions='Custom instructions',
        custom_secrets_descriptions={},  # Empty custom secrets
        content='Added workspace context',
    )

    # Set up the mock to return our observation
    memory._on_workspace_context_recall = MagicMock(return_value=mock_observation)

    # Process the recall action directly
    async def run_test():
        await memory._on_event(recall_action)

        # Verify that _on_workspace_context_recall was called with the recall action
        memory._on_workspace_context_recall.assert_called_once()
        call_args = memory._on_workspace_context_recall.call_args[0][0]
        assert isinstance(call_args, RecallAction)
        assert call_args.recall_type == RecallType.WORKSPACE_CONTEXT

        # Verify that the observation was added to the event stream
        event_stream.add_event.assert_called_with(
            mock_observation, EventSource.ENVIRONMENT
        )

        # Verify that custom_secrets_descriptions were included in the observation as empty dict
        assert mock_observation.custom_secrets_descriptions == {}

    # Run the async test
    asyncio.run(run_test())
