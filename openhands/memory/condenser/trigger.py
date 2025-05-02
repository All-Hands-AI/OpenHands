from abc import ABC, abstractmethod

from openhands.controller.agent import Agent, LLMCompletionProvider
from openhands.controller.state.state import State
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.action import ActionType
from openhands.events.event import EventSource
from openhands.memory.view import View


class Trigger(ABC):
    """Abstract interface for a trigger used by a condenser to decide,
    if to condense."""

    @abstractmethod
    def should_condense(
        self, view: View, state: State, agent: Agent | None = None
    ) -> bool:
        """Determine if the view should be condensed."""
        pass

    def __or__(self, value) -> 'OrTrigger':
        return OrTrigger(self, value)  # type: ignore


class OrTrigger(Trigger):
    """Trigger that combines multiple triggers with a logical OR."""

    def __init__(self, *triggers: Trigger):
        """Initialize the trigger with a list of triggers."""
        self.triggers = triggers

    def should_condense(
        self, view: View, state: State, agent: Agent | None = None
    ) -> bool:
        """Check if any triggers should condense."""
        return any(
            trigger.should_condense(view, state, agent) for trigger in self.triggers
        )


class EventCountTrigger(Trigger):
    """Trigger that checks if the number of events exceeds a specified limit."""

    def __init__(self, max_events: int):
        """Initialize the trigger with a maximum number of events."""
        self.max_events = max_events

    def should_condense(
        self, view: View, state: State, agent: Agent | None = None
    ) -> bool:
        """Check if the number of events exceeds the maximum limit."""
        if len(view.events) > self.max_events:
            logger.info(f'Condensing events due to max size({self.max_events}) limit.')
            return True
        return False


class KeywordTrigger(Trigger):
    """Trigger that checks for a specific keyword in the last user message."""

    def __init__(self, trigger_word: str):
        """Initialize the trigger with a specific keyword."""
        self.trigger_word = trigger_word

    def should_condense(
        self, view: View, state: State, agent: Agent | None = None
    ) -> bool:
        """Check if the last user message contains the trigger word."""
        events = view.events
        if not events or len(events) < 2:  # Need at least 2 events to condense
            return False

        # Iterate through events in reverse order to find the last user message
        for event in reversed(events):
            if (
                hasattr(event, 'source')
                and event.source == EventSource.USER
                and hasattr(event, 'action')
                and event.action == ActionType.MESSAGE  # type: ignore
                and event.message is not None
            ):
                if self.trigger_word in event.message:
                    logger.info(
                        f"Condensing events due to trigger word '{self.trigger_word}'."
                    )
                    return True
                else:
                    return False

            # If we did a condensation, stop looking
            if hasattr(event, 'action') and event.action == ActionType.CONDENSATION:  # type: ignore
                return False

        return False


class ConversationTokenTrigger(Trigger):
    """Trigger that checks if the number of tokens in the conversation exceeds a specified limit."""

    def __init__(self, max_tokens: int):
        """Initialize the trigger with a maximum number of tokens."""
        self.max_tokens = max_tokens

    def should_condense(
        self, view: View, state: State, agent: Agent | None = None
    ) -> bool:
        """Check if the number of tokens exceeds the maximum limit."""
        if (
            agent is not None
            and hasattr(agent, 'llm')
            and hasattr(agent.llm, 'get_token_count')
            and isinstance(agent, LLMCompletionProvider)
        ):
            messages = agent.get_messages(
                view.events, agent._get_initial_user_message(view.events)
            )
            token_count = agent.llm.get_token_count(messages)

            if token_count > self.max_tokens:
                logger.info(
                    f'Condensing events due to token count ({token_count}) exceeding limit ({self.max_tokens}).'
                )
                return True

            logger.debug(f'Current token count: {token_count}/{self.max_tokens}')
        return False
