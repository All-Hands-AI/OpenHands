import pathlib
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.schema import AgentState
from openhands.events.action import (
    ChangeAgentStateAction,
    CmdRunAction,
    IPythonRunCellAction,
)
from openhands.events.action.action import ActionConfirmationStatus, ActionSecurityRisk
from openhands.events.event import EventSource
from openhands.events.stream import EventStream
from openhands.security.invariant import InvariantAnalyzer
from openhands.security.invariant.client import InvariantClient
from openhands.storage import get_file_store


@pytest.fixture
def temp_dir():
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path(temp_dir).mkdir(parents=True, exist_ok=True)
        yield temp_dir


@pytest.mark.asyncio
async def test_security_analyzer_blocks_high_risk_action(temp_dir):
    """Test that high-risk actions are blocked by the security analyzer."""
    # Set up the event stream
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('main', file_store)

    # Create a dangerous command action
    dangerous_action = CmdRunAction(
        command='rm -rf /', thought='Deleting root directory'
    )
    dangerous_action._source = EventSource.AGENT

    # Mock the Docker and HTTP clients
    mock_container = MagicMock()
    mock_container.status = 'running'
    mock_container.attrs = {
        'NetworkSettings': {'Ports': {'8000/tcp': [{'HostPort': '34567'}]}}
    }
    mock_docker = MagicMock()
    mock_docker.from_env().containers.list.return_value = [mock_container]

    mock_httpx = MagicMock()
    mock_httpx.get().json.return_value = {'id': 'mock-session-id'}
    mock_httpx.post().json.side_effect = [
        {'monitor_id': 'mock-monitor-id'},
        [
            'PolicyViolation(Disallow rm -rf [risk=high], ranges=[<2 ranges>])'
        ],  # Security check response
    ]

    # Create a policy that marks 'rm -rf' commands as high risk
    policy = """
    raise "Disallow rm -rf [risk=high]" if:
        (call: ToolCall)
        call is tool:run
        match("rm -rf", call.function.arguments.command)
    """

    with (
        patch(f'{InvariantAnalyzer.__module__}.docker', mock_docker),
        patch(f'{InvariantClient.__module__}.httpx', mock_httpx),
    ):
        # Create the security analyzer
        security_analyzer = InvariantAnalyzer(event_stream, policy)

        # Add the action to the event stream
        event_stream.add_event(dangerous_action, EventSource.AGENT)

        # Manually call the security analyzer's on_event method
        await security_analyzer.on_event(dangerous_action)

        # Verify that the security risk was set to HIGH
        assert hasattr(dangerous_action, 'security_risk')
        assert dangerous_action.security_risk == ActionSecurityRisk.HIGH

        # Set the action to awaiting confirmation
        dangerous_action.confirmation_state = (
            ActionConfirmationStatus.AWAITING_CONFIRMATION
        )

        # Verify that the security analyzer would confirm the action
        assert not await security_analyzer.should_confirm(dangerous_action)


@pytest.mark.asyncio
async def test_security_analyzer_allows_low_risk_action(temp_dir):
    """Test that low-risk actions are allowed by the security analyzer."""
    # Set up the event stream
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('main', file_store)

    # Create a safe command action
    safe_action = CmdRunAction(command='ls -la', thought='Listing files')
    safe_action._source = EventSource.AGENT

    # Mock the Docker and HTTP clients
    mock_container = MagicMock()
    mock_container.status = 'running'
    mock_container.attrs = {
        'NetworkSettings': {'Ports': {'8000/tcp': [{'HostPort': '34567'}]}}
    }
    mock_docker = MagicMock()
    mock_docker.from_env().containers.list.return_value = [mock_container]

    mock_httpx = MagicMock()
    mock_httpx.get().json.return_value = {'id': 'mock-session-id'}
    mock_httpx.post().json.side_effect = [
        {'monitor_id': 'mock-monitor-id'},
        [],  # Security check response - no violations
    ]

    # Create a policy that marks 'rm -rf' commands as high risk (but we'll use a safe command)
    policy = """
    raise "Disallow rm -rf [risk=high]" if:
        (call: ToolCall)
        call is tool:run
        match("rm -rf", call.function.arguments.command)
    """

    with (
        patch(f'{InvariantAnalyzer.__module__}.docker', mock_docker),
        patch(f'{InvariantClient.__module__}.httpx', mock_httpx),
    ):
        # Create the security analyzer
        security_analyzer = InvariantAnalyzer(event_stream, policy)

        # Add the action to the event stream
        event_stream.add_event(safe_action, EventSource.AGENT)

        # Manually call the security analyzer's on_event method
        await security_analyzer.on_event(safe_action)

        # Verify that the security risk was set to LOW
        assert hasattr(safe_action, 'security_risk')
        assert safe_action.security_risk == ActionSecurityRisk.LOW


@pytest.mark.asyncio
async def test_security_analyzer_medium_risk_with_confirmation(temp_dir):
    """Test that medium-risk actions require confirmation when confirmation mode is enabled."""
    # Set up the event stream
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('main', file_store)

    # Create a medium-risk Python action
    medium_risk_action = IPythonRunCellAction(
        code="import os\nos.system('echo hello')", thought='Running system command'
    )
    medium_risk_action._source = EventSource.AGENT

    # Mock the Docker and HTTP clients
    mock_container = MagicMock()
    mock_container.status = 'running'
    mock_container.attrs = {
        'NetworkSettings': {'Ports': {'8000/tcp': [{'HostPort': '34567'}]}}
    }
    mock_docker = MagicMock()
    mock_docker.from_env().containers.list.return_value = [mock_container]

    mock_httpx = MagicMock()
    mock_httpx.get().json.return_value = {'id': 'mock-session-id'}
    mock_httpx.post().json.side_effect = [
        {'monitor_id': 'mock-monitor-id'},
        [
            'PolicyViolation(Potentially unsafe code [risk=medium], ranges=[<2 ranges>])'
        ],  # Security check response
    ]

    # Create a policy that marks certain Python code as medium risk
    policy = """
    raise "Potentially unsafe code [risk=medium]" if:
        (call: ToolCall)
        call is tool:run_ipython
        match("os.system", call.function.arguments.code)
    """

    with (
        patch(f'{InvariantAnalyzer.__module__}.docker', mock_docker),
        patch(f'{InvariantClient.__module__}.httpx', mock_httpx),
    ):
        # Create the security analyzer
        security_analyzer = InvariantAnalyzer(event_stream, policy)

        # Set the RISK_SEVERITY setting to HIGH (so MEDIUM risk actions need confirmation)
        security_analyzer.settings = {'RISK_SEVERITY': ActionSecurityRisk.HIGH}
        # Add the action to the event stream
        event_stream.add_event(medium_risk_action, EventSource.AGENT)

        # Manually call the security analyzer's on_event method
        await security_analyzer.on_event(medium_risk_action)

        # Verify that the security risk was set to MEDIUM
        assert hasattr(medium_risk_action, 'security_risk')
        assert medium_risk_action.security_risk == ActionSecurityRisk.MEDIUM

        # Set the action to awaiting confirmation
        medium_risk_action.confirmation_state = (
            ActionConfirmationStatus.AWAITING_CONFIRMATION
        )

        # Verify that the security analyzer would confirm the action
        assert await security_analyzer.should_confirm(medium_risk_action)

        # Mock the add_event method to capture the confirmation action
        original_add_event = event_stream.add_event
        confirmation_actions = []

        def mock_add_event(event, source):
            if isinstance(event, ChangeAgentStateAction):
                confirmation_actions.append(event)
            return original_add_event(event, source)

        event_stream.add_event = mock_add_event

        # Call the confirm method
        await security_analyzer.confirm(medium_risk_action)

        # Verify that a confirmation action was added
        assert len(confirmation_actions) > 0
        assert isinstance(confirmation_actions[0], ChangeAgentStateAction)
        assert confirmation_actions[0].agent_state == AgentState.USER_CONFIRMED


@pytest.mark.asyncio
async def test_security_analyzer_user_rejection(temp_dir):
    """Test that actions can be rejected by the user."""
    # Set up the event stream
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('main', file_store)

    # Create a medium-risk command action
    medium_risk_action = CmdRunAction(
        command='wget https://example.com/file.sh -O /tmp/file.sh',
        thought='Downloading a file',
    )
    medium_risk_action._source = EventSource.AGENT

    # Mock the Docker and HTTP clients
    mock_container = MagicMock()
    mock_container.status = 'running'
    mock_container.attrs = {
        'NetworkSettings': {'Ports': {'8000/tcp': [{'HostPort': '34567'}]}}
    }
    mock_docker = MagicMock()
    mock_docker.from_env().containers.list.return_value = [mock_container]

    mock_httpx = MagicMock()
    mock_httpx.get().json.return_value = {'id': 'mock-session-id'}
    mock_httpx.post().json.side_effect = [
        {'monitor_id': 'mock-monitor-id'},
        [
            'PolicyViolation(Potentially unsafe command [risk=medium], ranges=[<2 ranges>])'
        ],  # Security check response
    ]

    # Create a policy that marks certain commands as medium risk
    policy = """
    raise "Potentially unsafe command [risk=medium]" if:
        (call: ToolCall)
        call is tool:run
        match("wget", call.function.arguments.command)
    """

    with (
        patch(f'{InvariantAnalyzer.__module__}.docker', mock_docker),
        patch(f'{InvariantClient.__module__}.httpx', mock_httpx),
    ):
        # Create the security analyzer
        # Set the RISK_SEVERITY setting to HIGH (so MEDIUM risk actions need confirmation)
        security_analyzer = InvariantAnalyzer(event_stream, policy)

        # Set the RISK_SEVERITY setting to HIGH (so MEDIUM risk actions need confirmation)
        security_analyzer.settings = {'RISK_SEVERITY': ActionSecurityRisk.HIGH}

        # Add the action to the event stream
        event_stream.add_event(medium_risk_action, EventSource.AGENT)

        # Manually call the security analyzer's on_event method
        await security_analyzer.on_event(medium_risk_action)

        # Verify that the security risk was set to MEDIUM
        assert hasattr(medium_risk_action, 'security_risk')
        assert medium_risk_action.security_risk == ActionSecurityRisk.MEDIUM

        # Set the action to awaiting confirmation
        medium_risk_action.confirmation_state = (
            ActionConfirmationStatus.AWAITING_CONFIRMATION
        )

        # Verify that the security analyzer would confirm the action
        assert await security_analyzer.should_confirm(medium_risk_action)

        # Set the action to rejected
        medium_risk_action.confirmation_state = ActionConfirmationStatus.REJECTED

        # Verify that the security analyzer would not confirm the action
        assert not await security_analyzer.should_confirm(medium_risk_action)
