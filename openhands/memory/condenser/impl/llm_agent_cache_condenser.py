from __future__ import annotations

from typing import Any

from openhands.controller.state.state import State
from openhands.core.config.condenser_config import LLMAgentCacheCondenserConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.core.schema.action import ActionType
from openhands.events.action.agent import CondensationAction
from openhands.events.action.message import MessageAction
from openhands.events.event import Event, EventSource
from openhands.memory.condenser.condenser import Condensation, View
from openhands.memory.condenser.impl.caching_condenser import CachingCondenser


class LLMAgentCacheCondenser(CachingCondenser):
    """A version of LLMSummarizingCondenser that uses a caching."""

    def __init__(
        self,
        max_size: int = 100,
        trigger_word: str = 'CONDENSE!',
        keep_user_messages: bool = False,
        keep_first: int = 1,
    ):
        """Initialize the condenser.
        Args:
            max_size: Maximum number of events before condensation is triggered
            trigger_word: Word that triggers condensation when found in user messages
            keep_first: Number of initial events to always retain
        """
        if keep_first >= max_size:
            raise ValueError(
                f'keep_first ({keep_first}) must be less than max_size ({max_size})'
            )
        if keep_first < 0:
            raise ValueError(f'keep_first ({keep_first}) cannot be negative')

        self.keep_first = keep_first
        self.max_size = max_size
        self.trigger_word = trigger_word
        self.keep_user_messages = keep_user_messages
        super().__init__()

    def createCondensationPrompt(
        self, events: list[Event], state: State, base_messages: list[Message]
    ) -> Message:
        """Create the prompt for condensation using a similar approach to LLMSummarizingCondenser.
        This method is required by the CachingCondenser abstract base class.
        Args:
            events: The events to condense
            state: The current state
            base_messages: The messages that are already in the prompt (cached)
        Returns:
            The message with condensation instructions
        """
        # Create the condensation instructions similar to LLMSummarizingCondenser
        prompt = """You are maintaining a context-aware state summary for an interactive agent. 
The whole conversation above will be removed from the context window. Therefore you need to track:

USER_CONTEXT: (Preserve essential user requirements, goals, and clarifications in concise form)

COMPLETED: (Tasks completed so far, with brief results)
PENDING: (Tasks that still need to be done)
CURRENT_STATE: (Current variables, data structures, or relevant state)

For code-specific tasks, also include:
CODE_STATE: {File paths, function signatures, data structures}
TESTS: {Failing cases, error messages, outputs}
CHANGES: {Code edits, variable updates}
DEPS: {Dependencies, imports, external calls}
VERSION_CONTROL_STATUS: {Repository state, current branch, PR status, commit history}

PRIORITIZE:
1. Adapt tracking format to match the actual task type
2. Capture key user requirements and goals
3. Distinguish between completed and pending tasks
4. Keep all sections concise and relevant

SKIP: Tracking irrelevant details for the current task type

Example formats:

For code tasks:
USER_CONTEXT: Fix FITS card float representation issue
COMPLETED: Modified mod_float() in card.py, all tests passing
PENDING: Create PR, update documentation
CODE_STATE: mod_float() in card.py updated
TESTS: test_format() passed
CHANGES: str(val) replaces f"{val:.16G}"
DEPS: None modified
VERSION_CONTROL_STATUS: Branch: fix-float-precision, Latest commit: a1b2c3d

For other tasks:
USER_CONTEXT: Write 20 haikus based on coin flip results
COMPLETED: 15 haikus written for results [T,H,T,H,T,H,T,T,H,T,H,T,H,T,H]
PENDING: 5 more haikus needed
CURRENT_STATE: Last flip: Heads, Haiku count: 15/20"""

        prompt += '\n\n'

        # Create a message with the condensation instructions
        return Message(
            role='user',
            content=[TextContent(text=prompt)],
        )

    def processResponse(
        self, events: list[Event], state: State, response: Any, messages: list[Message]
    ) -> Condensation | View:
        # Extract the summary from the response
        summary = response.choices[0].message.content

        # Keep the first `keep_first` events (e.g., system messages)
        events_to_keep = events[: self.keep_first]
        events_to_forget = events[self.keep_first :]

        # Ensure essential user messages are not forgotten
        if self.keep_user_messages:
            self._filter_user_messages_to_keep(events, events_to_forget)

        # If we have events to forget, create a condensation
        if events_to_forget:
            forgotten_event_ids = [event.id for event in events_to_forget]

            return Condensation(
                action=CondensationAction(
                    forgotten_event_ids=forgotten_event_ids, summary=summary
                )
            )
        else:
            return View(events=events_to_keep + events_to_forget)

    def should_condense(self, view: View) -> bool:
        """Determine if the view should be condensed.
        Condensation is triggered in two cases:
        1. When the number of events exceeds max_size
        2. When the last event is from the user and contains the trigger word
        Args:
            view: The view to check
        Returns:
            True if the view should be condensed, False otherwise
        """
        events = view.events

        # Check if the number of events exceeds max_size
        if len(events) > self.max_size:
            logger.info(f'Condensing events due to max size({self.max_size}) limit.')
            return True

        # Check if any recent user message contains the trigger word
        if self._contains_trigger_word(events):
            logger.info(f"Condensing events due to trigger word '{self.trigger_word}'.")
            return True

        return False

    def _contains_trigger_word(self, events: list[Event]) -> bool:
        """Check if the most recent user message contains the trigger word.
        Args:
            events: The events to check
        Returns:
            True if the most recent user message contains the trigger word, False otherwise
        """
        if not events or len(events) < 2:  # Need at least 2 events to condense
            return False

        # Iterate through events in reverse order to find the last user message
        for event in reversed(events):
            if (
                hasattr(event, 'source')
                and event.source == EventSource.USER
                and hasattr(event, 'action')
                and event.action == ActionType.MESSAGE
                and event.message is not None
            ):
                return self.trigger_word in event.message

            # If we did a condensation, stop looking
            if hasattr(event, 'action') and event.action == ActionType.CONDENSATION:
                return False

        return False

    def _filter_user_messages_to_keep(
        self, events: list[Event], events_to_forget: list[Event]
    ) -> None:
        """Ensure essential user messages are not forgotten."""
        user_events = [event for event in events if isinstance(event, MessageAction)]

        # Always keep the first user message to maintain context
        first_user_message = next((event for event in user_events), None)
        if first_user_message and first_user_message in events_to_forget:
            events_to_forget.remove(first_user_message)

        # Also keep the most recent user message if it's different from the first
        if len(user_events) > 1:
            last_user_message = user_events[-1]
            if (
                last_user_message != first_user_message
                and last_user_message in events_to_forget
            ):
                events_to_forget.remove(last_user_message)

    @classmethod
    def from_config(
        cls, config: LLMAgentCacheCondenserConfig
    ) -> LLMAgentCacheCondenser:
        return LLMAgentCacheCondenser(
            max_size=config.max_size,
            trigger_word=config.trigger_word,
            keep_first=config.keep_first,
        )


LLMAgentCacheCondenser.register_config(LLMAgentCacheCondenserConfig)
