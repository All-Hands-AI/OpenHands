"""Tests for enterprise integrations utils module."""

import pytest
from integrations.utils import get_summary_for_agent_state

from openhands.core.schema.agent import AgentState
from openhands.events.observation.agent import AgentStateChangedObservation


class TestGetSummaryForAgentState:
    """Test cases for get_summary_for_agent_state function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.conversation_link = 'https://example.com/conversation/123'

    def test_empty_observations_list(self):
        """Test handling of empty observations list."""
        result = get_summary_for_agent_state([], self.conversation_link)

        assert 'unknown error' in result.lower()
        assert self.conversation_link in result

    @pytest.mark.parametrize(
        'state,expected_text,includes_link',
        [
            (AgentState.RATE_LIMITED, 'rate limited', False),
            (AgentState.AWAITING_USER_INPUT, 'waiting for your input', True),
        ],
    )
    def test_handled_agent_states(self, state, expected_text, includes_link):
        """Test handling of states with specific behavior."""
        observation = AgentStateChangedObservation(
            content=f'Agent state: {state.value}', agent_state=state
        )

        result = get_summary_for_agent_state([observation], self.conversation_link)

        assert expected_text in result.lower()
        if includes_link:
            assert self.conversation_link in result
        else:
            assert self.conversation_link not in result

    @pytest.mark.parametrize(
        'state',
        [
            AgentState.FINISHED,
            AgentState.PAUSED,
            AgentState.STOPPED,
            AgentState.AWAITING_USER_CONFIRMATION,
        ],
    )
    def test_unhandled_agent_states(self, state):
        """Test handling of unhandled states (should all return unknown error)."""
        observation = AgentStateChangedObservation(
            content=f'Agent state: {state.value}', agent_state=state
        )

        result = get_summary_for_agent_state([observation], self.conversation_link)

        assert 'unknown error' in result.lower()
        assert self.conversation_link in result

    @pytest.mark.parametrize(
        'error_code,expected_text',
        [
            (
                'STATUS$ERROR_LLM_AUTHENTICATION',
                'authentication with the llm provider failed',
            ),
            (
                'STATUS$ERROR_LLM_SERVICE_UNAVAILABLE',
                'llm service is temporarily unavailable',
            ),
            (
                'STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR',
                'llm provider encountered an internal error',
            ),
            ('STATUS$ERROR_LLM_OUT_OF_CREDITS', "you've run out of credits"),
            ('STATUS$ERROR_LLM_CONTENT_POLICY_VIOLATION', 'content policy violation'),
        ],
    )
    def test_error_state_readable_reasons(self, error_code, expected_text):
        """Test all readable error reason mappings."""
        observation = AgentStateChangedObservation(
            content=f'Agent encountered error: {error_code}',
            agent_state=AgentState.ERROR,
            reason=error_code,
        )

        result = get_summary_for_agent_state([observation], self.conversation_link)

        assert 'encountered an error' in result.lower()
        assert expected_text in result.lower()
        assert self.conversation_link in result

    def test_error_state_with_custom_reason(self):
        """Test handling of ERROR state with a custom reason."""
        observation = AgentStateChangedObservation(
            content='Agent encountered an error',
            agent_state=AgentState.ERROR,
            reason='Test error message',
        )

        result = get_summary_for_agent_state([observation], self.conversation_link)

        assert 'encountered an error' in result.lower()
        assert 'test error message' in result.lower()
        assert self.conversation_link in result

    def test_multiple_observations_uses_first(self):
        """Test that when multiple observations are provided, only the first is used."""
        observation1 = AgentStateChangedObservation(
            content='Agent is awaiting user input',
            agent_state=AgentState.AWAITING_USER_INPUT,
        )
        observation2 = AgentStateChangedObservation(
            content='Agent encountered an error',
            agent_state=AgentState.ERROR,
            reason='Should not be used',
        )

        result = get_summary_for_agent_state(
            [observation1, observation2], self.conversation_link
        )

        # Should handle the first observation (AWAITING_USER_INPUT), not the second (ERROR)
        assert 'waiting for your input' in result.lower()
        assert 'error' not in result.lower()

    def test_awaiting_user_input_specific_message(self):
        """Test that AWAITING_USER_INPUT returns the specific expected message."""
        observation = AgentStateChangedObservation(
            content='Agent is awaiting user input',
            agent_state=AgentState.AWAITING_USER_INPUT,
        )

        result = get_summary_for_agent_state([observation], self.conversation_link)

        # Test the exact message format
        assert 'waiting for your input' in result.lower()
        assert 'continue the conversation' in result.lower()
        assert self.conversation_link in result
        assert 'unknown error' not in result.lower()

    def test_rate_limited_specific_message(self):
        """Test that RATE_LIMITED returns the specific expected message."""
        observation = AgentStateChangedObservation(
            content='Agent was rate limited', agent_state=AgentState.RATE_LIMITED
        )

        result = get_summary_for_agent_state([observation], self.conversation_link)

        # Test the exact message format
        assert 'rate limited' in result.lower()
        assert 'try again later' in result.lower()
        # RATE_LIMITED doesn't include conversation link in response
        assert self.conversation_link not in result
