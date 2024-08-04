from enum import Enum

from opendevin.events.action import (
    Action,
    AgentDelegateAction,
    MessageAction,
)

from .prompt import (
    ADAPT_PROMPT,
    IMPLEMENT_PROMPT,
    SELECT_PROMPT,
)


class SelfDiscoverState(Enum):
    SELECT = 0
    ADAPT = 1
    IMPLEMENT = 2
    SOLVE = 3


class SelfDiscoverStateMachine:
    def __init__(self) -> None:
        self.current_state: SelfDiscoverState = SelfDiscoverState.SELECT
        self.prev_state: SelfDiscoverState | None = None

    def reset(self) -> None:
        self.current_state = SelfDiscoverState.SELECT
        self.prev_state = None

    def transition(self, action: Action) -> None:
        self.prev_state = self.current_state
        # Only move to next state if not browsing or user inquiry
        if not (
            (
                isinstance(action, AgentDelegateAction)
                and action.agent == 'BrowsingAgent'
            )
            or (isinstance(action, MessageAction) and action.wait_for_response)
        ):
            if self.current_state != SelfDiscoverState.SOLVE:
                self.current_state = SelfDiscoverState(self.current_state.value + 1)

    def get_prompt(self) -> dict[str, str] | None:
        if self.current_state == SelfDiscoverState.SELECT:
            content = SELECT_PROMPT
        elif self.current_state == SelfDiscoverState.ADAPT:
            content = ADAPT_PROMPT
        elif self.current_state == SelfDiscoverState.IMPLEMENT:
            content = IMPLEMENT_PROMPT
        else:
            return None

        return {
            'role': 'user',
            'content': content,
        }
