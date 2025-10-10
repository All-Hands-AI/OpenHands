from typing import Any, Self
from unittest.mock import patch

import pytest
from openhands_cli.runner import ConversationRunner
from openhands_cli.user_actions.types import UserConfirmation
from pydantic import ConfigDict, SecretStr, model_validator

from openhands.sdk import Conversation, ConversationCallbackType
from openhands.sdk.agent.base import AgentBase
from openhands.sdk.conversation import ConversationState
from openhands.sdk.conversation.state import AgentExecutionStatus
from openhands.sdk.llm import LLM
from openhands.sdk.security.confirmation_policy import AlwaysConfirm, NeverConfirm


class FakeLLM(LLM):
    @model_validator(mode='after')
    def _set_env_side_effects(self) -> Self:
        return self


def default_config() -> dict[str, Any]:
    return {
        'model': 'gpt-4o',
        'api_key': SecretStr('test_key'),
        'num_retries': 2,
        'retry_min_wait': 1,
        'retry_max_wait': 2,
    }


class FakeAgent(AgentBase):
    model_config = ConfigDict(frozen=False)
    step_count: int = 0
    finish_on_step: int | None = None

    def init_state(
        self, state: ConversationState, on_event: ConversationCallbackType
    ) -> None:
        pass

    def step(
        self, state: ConversationState, on_event: ConversationCallbackType
    ) -> None:
        self.step_count += 1
        if self.step_count == self.finish_on_step:
            state.agent_status = AgentExecutionStatus.FINISHED


@pytest.fixture()
def agent() -> FakeAgent:
    llm = LLM(**default_config(), service_id='test-service')
    return FakeAgent(llm=llm, tools=[])


class TestConversationRunner:
    @pytest.mark.parametrize(
        'agent_status', [AgentExecutionStatus.RUNNING, AgentExecutionStatus.PAUSED]
    )
    def test_non_confirmation_mode_runs_once(
        self, agent: FakeAgent, agent_status: AgentExecutionStatus
    ) -> None:
        """
        1. Confirmation mode is not on
        2. Process message resumes paused conversation or continues running conversation
        """

        convo = Conversation(agent)
        convo.max_iteration_per_run = 1
        convo.state.agent_status = agent_status
        cr = ConversationRunner(convo)
        cr.set_confirmation_policy(NeverConfirm())
        cr.process_message(message=None)

        assert agent.step_count == 1
        assert convo.state.agent_status != AgentExecutionStatus.PAUSED

    @pytest.mark.parametrize(
        'confirmation, final_status, expected_run_calls',
        [
            # Case 1: Agent waiting for confirmation; user DEFERS -> early return, no run()
            (UserConfirmation.DEFER, AgentExecutionStatus.WAITING_FOR_CONFIRMATION, 0),
            # Case 2: Agent waiting for confirmation; user ACCEPTS -> run() once, break (finished=True)
            (UserConfirmation.ACCEPT, AgentExecutionStatus.FINISHED, 1),
        ],
    )
    def test_confirmation_mode_waiting_and_user_decision_controls_run(
        self,
        agent: FakeAgent,
        confirmation: UserConfirmation,
        final_status: AgentExecutionStatus,
        expected_run_calls: int,
    ) -> None:
        """
        1. Agent may be paused but is waiting for consent on actions
        2. If paused, we should have asked for confirmation on action
        3. If not paused, we should still ask for confirmation on actions
        4. If deferred no run call to agent should be made
        5. If accepted, run call to agent should be made

        """
        if final_status == AgentExecutionStatus.FINISHED:
            agent.finish_on_step = 1
        
        # Add a mock security analyzer to enable confirmation mode
        from unittest.mock import MagicMock
        agent.security_analyzer = MagicMock()
        
        convo = Conversation(agent)
        convo.state.agent_status = AgentExecutionStatus.WAITING_FOR_CONFIRMATION
        cr = ConversationRunner(convo)
        cr.set_confirmation_policy(AlwaysConfirm())
        with patch.object(
            cr, '_handle_confirmation_request', return_value=confirmation
        ) as mock_confirmation_request:
            cr.process_message(message=None)
        mock_confirmation_request.assert_called_once()
        assert agent.step_count == expected_run_calls
        assert convo.state.agent_status == final_status

    def test_confirmation_mode_not_waiting__runs_once_when_finished_true(
        self, agent: FakeAgent
    ) -> None:
        """
        1. Agent was not waiting
        2. Agent finished without any actions
        3. Conversation should finished without asking user for instructions
        """
        agent.finish_on_step = 1
        convo = Conversation(agent)
        convo.state.agent_status = AgentExecutionStatus.PAUSED

        cr = ConversationRunner(convo)
        cr.set_confirmation_policy(AlwaysConfirm())

        with patch.object(cr, '_handle_confirmation_request') as _mock_h:
            cr.process_message(message=None)

        # No confirmation was needed up front; we still expect exactly one run.
        assert agent.step_count == 1
        _mock_h.assert_not_called()
