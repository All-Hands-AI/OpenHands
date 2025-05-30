import pathlib
import tempfile

import pytest

from openhands.events.action import (
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.action.action import ActionConfirmationStatus, ActionSecurityRisk
from openhands.events.event import EventSource
from openhands.events.stream import EventStream
from openhands.security.bully import BullySecurityAnalyzer
from openhands.security.pushover import PushoverSecurityAnalyzer
from openhands.storage import get_file_store


@pytest.fixture
def temp_dir():
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path(temp_dir).mkdir(parents=True, exist_ok=True)
        yield temp_dir


@pytest.mark.asyncio
async def test_pushover_security_analyzer_allows_all_actions(temp_dir):
    """Test that the PushoverSecurityAnalyzer allows all actions by marking them as low risk."""
    # Set up the event stream
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('main', file_store)

    # Create the security analyzer
    security_analyzer = PushoverSecurityAnalyzer(event_stream)

    # Create a potentially dangerous command action
    dangerous_action = CmdRunAction(
        command='rm -rf /', thought='Deleting root directory'
    )
    dangerous_action._source = EventSource.AGENT

    # Add the action to the event stream
    event_stream.add_event(dangerous_action, EventSource.AGENT)

    # Manually call the security analyzer's on_event method
    await security_analyzer.on_event(dangerous_action)

    # Verify that the security risk was set to LOW regardless of the action
    assert hasattr(dangerous_action, 'security_risk')
    assert dangerous_action.security_risk == ActionSecurityRisk.LOW

    # Create a safe command action
    safe_action = CmdRunAction(command='ls -la', thought='Listing files')
    safe_action._source = EventSource.AGENT

    # Add the action to the event stream
    event_stream.add_event(safe_action, EventSource.AGENT)

    # Manually call the security analyzer's on_event method
    await security_analyzer.on_event(safe_action)

    # Verify that the security risk was set to LOW
    assert hasattr(safe_action, 'security_risk')
    assert safe_action.security_risk == ActionSecurityRisk.LOW

    # Create a Python action
    python_action = IPythonRunCellAction(
        code="import os\nos.system('echo hello')", thought='Running system command'
    )
    python_action._source = EventSource.AGENT

    # Add the action to the event stream
    event_stream.add_event(python_action, EventSource.AGENT)

    # Manually call the security analyzer's on_event method
    await security_analyzer.on_event(python_action)

    # Verify that the security risk was set to LOW
    assert hasattr(python_action, 'security_risk')
    assert python_action.security_risk == ActionSecurityRisk.LOW


@pytest.mark.asyncio
async def test_bully_security_analyzer_blocks_all_actions(temp_dir):
    """Test that the BullySecurityAnalyzer blocks all actions by marking them as high risk."""
    # Set up the event stream
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('main', file_store)

    # Create the security analyzer
    security_analyzer = BullySecurityAnalyzer(event_stream)

    # Create a safe command action
    safe_action = CmdRunAction(command='ls -la', thought='Listing files')
    safe_action._source = EventSource.AGENT

    # Add the action to the event stream
    event_stream.add_event(safe_action, EventSource.AGENT)

    # Manually call the security analyzer's on_event method
    await security_analyzer.on_event(safe_action)

    # Verify that the security risk was set to HIGH regardless of the action
    assert hasattr(safe_action, 'security_risk')
    assert safe_action.security_risk == ActionSecurityRisk.HIGH

    # Create a harmless Python action
    python_action = IPythonRunCellAction(
        code="print('Hello, world!')", thought='Printing a message'
    )
    python_action._source = EventSource.AGENT

    # Add the action to the event stream
    event_stream.add_event(python_action, EventSource.AGENT)

    # Manually call the security analyzer's on_event method
    await security_analyzer.on_event(python_action)

    # Verify that the security risk was set to HIGH
    assert hasattr(python_action, 'security_risk')
    assert python_action.security_risk == ActionSecurityRisk.HIGH

    # Create a message action (which should be harmless)
    message_action = MessageAction(content='Hello, world!')
    message_action._source = EventSource.AGENT

    # Add the action to the event stream
    event_stream.add_event(message_action, EventSource.AGENT)

    # Manually call the security analyzer's on_event method
    await security_analyzer.on_event(message_action)

    # Verify that the security risk was set to HIGH
    assert hasattr(message_action, 'security_risk')
    assert message_action.security_risk == ActionSecurityRisk.HIGH


@pytest.mark.asyncio
async def test_security_analyzer_confirmation_behavior(temp_dir):
    """Test that the security analyzers correctly handle confirmation based on risk level."""
    # Set up the event stream
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('main', file_store)

    # Create the security analyzers
    pushover_analyzer = PushoverSecurityAnalyzer(event_stream)
    bully_analyzer = BullySecurityAnalyzer(event_stream)

    # Create a command action
    action = CmdRunAction(command='echo test', thought='Running echo')
    action._source = EventSource.AGENT

    # Set the action to awaiting confirmation
    action.confirmation_state = ActionConfirmationStatus.AWAITING_CONFIRMATION

    # Set the RISK_SEVERITY setting to HIGH (so MEDIUM and LOW risk actions need confirmation)
    pushover_analyzer.settings = {'RISK_SEVERITY': ActionSecurityRisk.HIGH}
    bully_analyzer.settings = {'RISK_SEVERITY': ActionSecurityRisk.HIGH}

    # Process with pushover analyzer
    await pushover_analyzer.on_event(action)

    # Verify that the security risk was set to LOW
    assert hasattr(action, 'security_risk')
    assert action.security_risk == ActionSecurityRisk.LOW

    # Verify that the pushover analyzer would confirm the action
    assert await pushover_analyzer.should_confirm(action)

    # Reset the action
    action.security_risk = None

    # Process with bully analyzer
    await bully_analyzer.on_event(action)

    # Verify that the security risk was set to HIGH
    assert hasattr(action, 'security_risk')
    assert action.security_risk == ActionSecurityRisk.HIGH

    # Verify that the bully analyzer would not confirm the action
    assert not await bully_analyzer.should_confirm(action)
