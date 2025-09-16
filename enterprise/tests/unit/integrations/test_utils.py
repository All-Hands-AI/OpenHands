"""Tests for enterprise integrations utils module."""

import pytest
from unittest.mock import patch, MagicMock

from openhands.core.schema.agent import AgentState
from openhands.events.observation.agent import AgentStateChangedObservation

from integrations.utils import get_summary_for_agent_state


class TestGetSummaryForAgentState:
    """Test cases for get_summary_for_agent_state function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.conversation_link = "https://example.com/conversation/123"

    def test_empty_observations_list(self):
        """Test handling of empty observations list."""
        with patch('integrations.utils.logger') as mock_logger:
            result = get_summary_for_agent_state([], self.conversation_link)
            
            assert "unknown error" in result.lower()
            assert self.conversation_link in result
            mock_logger.error.assert_called_once()

    @pytest.mark.parametrize("state,expected_text,expected_log_level,includes_link", [
        (AgentState.RATE_LIMITED, "rate limited", "warning", False),
        (AgentState.AWAITING_USER_INPUT, "waiting for your input", "info", True),
    ])
    def test_handled_agent_states(self, state, expected_text, expected_log_level, includes_link):
        """Test handling of states with specific behavior."""
        observation = AgentStateChangedObservation(
            content=f"Agent state: {state.value}",
            agent_state=state
        )
        
        with patch('integrations.utils.logger') as mock_logger:
            result = get_summary_for_agent_state([observation], self.conversation_link)
            
            assert expected_text in result.lower()
            if includes_link:
                assert self.conversation_link in result
            else:
                assert self.conversation_link not in result
            
            # Check correct log level was called
            if expected_log_level == "warning":
                mock_logger.warning.assert_called_once()
            elif expected_log_level == "info":
                mock_logger.info.assert_called_once()

    @pytest.mark.parametrize("state", [
        AgentState.FINISHED,
        AgentState.PAUSED,
        AgentState.STOPPED,
        AgentState.AWAITING_USER_CONFIRMATION,
    ])
    def test_unhandled_agent_states(self, state):
        """Test handling of unhandled states (should all return unknown error)."""
        observation = AgentStateChangedObservation(
            content=f"Agent state: {state.value}",
            agent_state=state
        )
        
        with patch('integrations.utils.logger') as mock_logger:
            result = get_summary_for_agent_state([observation], self.conversation_link)
            
            assert "unknown error" in result.lower()
            assert self.conversation_link in result
            mock_logger.error.assert_called_once()
            
            # Verify the error log contains the correct state information
            error_call = mock_logger.error.call_args
            assert "Unhandled agent state" in error_call[0][0]
            assert error_call[1]['extra']['agent_state'] == state.value

    @pytest.mark.parametrize("error_code,expected_text", [
        ('STATUS$ERROR_LLM_AUTHENTICATION', 'authentication with the llm provider failed'),
        ('STATUS$ERROR_LLM_SERVICE_UNAVAILABLE', 'llm service is temporarily unavailable'),
        ('STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR', 'llm provider encountered an internal error'),
        ('STATUS$ERROR_LLM_OUT_OF_CREDITS', "you've run out of credits"),
        ('STATUS$ERROR_LLM_CONTENT_POLICY_VIOLATION', 'content policy violation'),
    ])
    def test_error_state_readable_reasons(self, error_code, expected_text):
        """Test all readable error reason mappings."""
        observation = AgentStateChangedObservation(
            content=f"Agent encountered error: {error_code}",
            agent_state=AgentState.ERROR,
            reason=error_code
        )
        
        with patch('integrations.utils.logger') as mock_logger:
            result = get_summary_for_agent_state([observation], self.conversation_link)
            
            assert "encountered an error" in result.lower()
            assert expected_text in result.lower()
            assert self.conversation_link in result
            mock_logger.error.assert_called_once()

    def test_error_state_with_custom_reason(self):
        """Test handling of ERROR state with a custom reason."""
        observation = AgentStateChangedObservation(
            content="Agent encountered an error",
            agent_state=AgentState.ERROR,
            reason="Test error message"
        )
        
        with patch('integrations.utils.logger') as mock_logger:
            result = get_summary_for_agent_state([observation], self.conversation_link)
            
            assert "encountered an error" in result.lower()
            assert "test error message" in result.lower()
            assert self.conversation_link in result
            mock_logger.error.assert_called_once()

    def test_observation_with_reason_attribute(self):
        """Test that observation reason is properly logged in extra data."""
        observation = AgentStateChangedObservation(
            content="Agent was rate limited",
            agent_state=AgentState.RATE_LIMITED,
            reason="Rate limit exceeded"
        )
        
        with patch('integrations.utils.logger') as mock_logger:
            get_summary_for_agent_state([observation], self.conversation_link)
            
            warning_call = mock_logger.warning.call_args
            assert warning_call[1]['extra']['observation_reason'] == "Rate limit exceeded"

    def test_observation_without_reason_attribute(self):
        """Test handling of observation without reason attribute."""
        # Create a simple object without reason attribute
        class MockObservation:
            def __init__(self):
                self.agent_state = AgentState.AWAITING_USER_INPUT
                # No reason attribute
        
        mock_observation = MockObservation()
        
        with patch('integrations.utils.logger') as mock_logger:
            result = get_summary_for_agent_state([mock_observation], self.conversation_link)
            
            assert "waiting for your input" in result.lower()
            info_call = mock_logger.info.call_args
            # getattr(observation, 'reason', None) returns None when attribute doesn't exist
            assert info_call[1]['extra']['observation_reason'] is None

    def test_multiple_observations_uses_first(self):
        """Test that when multiple observations are provided, only the first is used."""
        observation1 = AgentStateChangedObservation(
            content="Agent is awaiting user input",
            agent_state=AgentState.AWAITING_USER_INPUT
        )
        observation2 = AgentStateChangedObservation(
            content="Agent encountered an error",
            agent_state=AgentState.ERROR,
            reason="Should not be used"
        )
        
        with patch('integrations.utils.logger') as mock_logger:
            result = get_summary_for_agent_state([observation1, observation2], self.conversation_link)
            
            # Should handle the first observation (AWAITING_USER_INPUT), not the second (ERROR)
            assert "waiting for your input" in result.lower()
            assert "error" not in result.lower()
            mock_logger.info.assert_called_once()

    def test_logging_extra_data_structure(self):
        """Test that logging extra data contains expected fields."""
        observation = AgentStateChangedObservation(
            content="Agent is awaiting user input",
            agent_state=AgentState.AWAITING_USER_INPUT,
            reason="test reason"
        )
        
        with patch('integrations.utils.logger') as mock_logger:
            get_summary_for_agent_state([observation], self.conversation_link)
            
            info_call = mock_logger.info.call_args
            extra_data = info_call[1]['extra']
            
            assert 'agent_state' in extra_data
            assert 'conversation_link' in extra_data
            assert 'observation_reason' in extra_data
            assert extra_data['agent_state'] == 'awaiting_user_input'
            assert extra_data['conversation_link'] == self.conversation_link
            assert extra_data['observation_reason'] == "test reason"