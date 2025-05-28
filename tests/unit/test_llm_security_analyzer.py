import pathlib
import tempfile
from unittest.mock import patch

import pytest

from openhands.core.config import LLMConfig
from openhands.events.action import (
    CmdRunAction,
    IPythonRunCellAction,
)
from openhands.events.action.action import ActionConfirmationStatus, ActionSecurityRisk
from openhands.events.event import EventSource
from openhands.events.stream import EventStream
from openhands.security.llm_analyzer import LLMSecurityAnalyzer
from openhands.storage import get_file_store


@pytest.fixture
def temp_dir():
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path(temp_dir).mkdir(parents=True, exist_ok=True)
        yield temp_dir


@pytest.fixture
def mock_llm_response():
    # Mock the LLM response for security analysis
    return {
        'choices': [
            {
                'message': {
                    'content': 'NO',
                    'role': 'assistant',
                }
            }
        ]
    }


@pytest.fixture
def mock_llm_dangerous_response():
    # Mock the LLM response for security analysis of dangerous actions
    return {
        'choices': [
            {
                'message': {
                    'content': 'YES',
                    'role': 'assistant',
                }
            }
        ]
    }


@pytest.mark.asyncio
async def test_llm_security_analyzer_safe_action(temp_dir, mock_llm_response):
    """Test that the LLMSecurityAnalyzer correctly identifies safe actions."""
    # Set up the event stream
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('main', file_store)

    # Create a mock LLM config
    llm_config = LLMConfig(model='gpt-4o', temperature=0.0)

    # Create a safe command action
    safe_action = CmdRunAction(command='ls -la', thought='Listing files')
    safe_action._source = EventSource.AGENT

    # Mock the LLM completion method
    with patch('openhands.llm.llm.litellm_completion', return_value=mock_llm_response):
        # Create the security analyzer
        security_analyzer = LLMSecurityAnalyzer(event_stream, llm_config)

        # Add the action to the event stream
        event_stream.add_event(safe_action, EventSource.AGENT)

        # Manually call the security analyzer's on_event method
        await security_analyzer.on_event(safe_action)

        # Verify that the security risk was set to LOW
        assert hasattr(safe_action, 'security_risk')
        assert safe_action.security_risk == ActionSecurityRisk.LOW

        # Set the action to awaiting confirmation
        safe_action.confirmation_state = ActionConfirmationStatus.AWAITING_CONFIRMATION

        # Set the RISK_SEVERITY setting to HIGH (so MEDIUM and LOW risk actions need confirmation)
        security_analyzer.settings = {'RISK_SEVERITY': ActionSecurityRisk.HIGH}

        # Verify that the security analyzer would confirm the action
        assert await security_analyzer.should_confirm(safe_action)


@pytest.mark.asyncio
async def test_llm_security_analyzer_dangerous_action(
    temp_dir, mock_llm_dangerous_response
):
    """Test that the LLMSecurityAnalyzer correctly identifies dangerous actions."""
    # Set up the event stream
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('main', file_store)

    # Create a mock LLM config
    llm_config = LLMConfig(model='gpt-4o', temperature=0.0)

    # Create a dangerous command action
    dangerous_action = CmdRunAction(
        command='rm -rf /', thought='Deleting root directory'
    )
    dangerous_action._source = EventSource.AGENT

    # Mock the LLM completion method
    with patch(
        'openhands.llm.llm.litellm_completion', return_value=mock_llm_dangerous_response
    ):
        # Create the security analyzer
        security_analyzer = LLMSecurityAnalyzer(event_stream, llm_config)

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

        # Set the RISK_SEVERITY setting to HIGH (so MEDIUM and LOW risk actions need confirmation)
        security_analyzer.settings = {'RISK_SEVERITY': ActionSecurityRisk.HIGH}

        # Verify that the security analyzer would not confirm the action
        assert not await security_analyzer.should_confirm(dangerous_action)


@pytest.mark.asyncio
async def test_llm_security_analyzer_python_code(
    temp_dir, mock_llm_response, mock_llm_dangerous_response
):
    """Test that the LLMSecurityAnalyzer correctly evaluates Python code."""
    # Set up the event stream
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('main', file_store)

    # Create a mock LLM config
    llm_config = LLMConfig(model='gpt-4o', temperature=0.0)

    # Create a safe Python action
    safe_code = IPythonRunCellAction(
        code="print('Hello, world!')", thought='Printing a message'
    )
    safe_code._source = EventSource.AGENT

    # Create a dangerous Python action
    dangerous_code = IPythonRunCellAction(
        code="import os\nos.system('rm -rf /')", thought='Running system command'
    )
    dangerous_code._source = EventSource.AGENT

    # Mock the LLM completion method for safe code
    with patch('openhands.llm.llm.litellm_completion', return_value=mock_llm_response):
        # Create the security analyzer
        security_analyzer = LLMSecurityAnalyzer(event_stream, llm_config)

        # Add the action to the event stream
        event_stream.add_event(safe_code, EventSource.AGENT)

        # Manually call the security analyzer's on_event method
        await security_analyzer.on_event(safe_code)

        # Verify that the security risk was set to LOW
        assert hasattr(safe_code, 'security_risk')
        assert safe_code.security_risk == ActionSecurityRisk.LOW

    # Mock the LLM completion method for dangerous code
    with patch(
        'openhands.llm.llm.litellm_completion', return_value=mock_llm_dangerous_response
    ):
        # Create a new security analyzer
        security_analyzer = LLMSecurityAnalyzer(event_stream, llm_config)

        # Add the action to the event stream
        event_stream.add_event(dangerous_code, EventSource.AGENT)

        # Manually call the security analyzer's on_event method
        await security_analyzer.on_event(dangerous_code)

        # Verify that the security risk was set to HIGH
        assert hasattr(dangerous_code, 'security_risk')
        assert dangerous_code.security_risk == ActionSecurityRisk.HIGH
