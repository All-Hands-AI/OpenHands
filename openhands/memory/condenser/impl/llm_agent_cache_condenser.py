from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Tuple, Union

from openhands.controller.state.state import State
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.core.schema.action import ActionType
from openhands.events.action.agent import CondensationAction
from openhands.events.event import Event, EventSource
from openhands.memory.condenser.condenser import Condensation, View
from openhands.memory.condenser.impl.caching_condenser import CachingCondenser

if TYPE_CHECKING:
    from typing import Optional

    from openhands.controller.agent import Agent


class LLMAgentCacheCondenser(CachingCondenser):
    def __init__(
        self,
        agent: Optional['Agent'] = None,
        max_size: int = 100,
        trigger_word: str = 'CONDENSE!',
    ):
        """Initialize the condenser.
        Args:
            agent: Optional agent instance for agent-aware condensation
            max_size: Maximum number of events before condensation is triggered
            trigger_word: Word that triggers condensation when found in user messages
        """
        self.agent = agent
        self.max_size = max_size
        self.trigger_word = trigger_word
        super().__init__()

    def createCondensationPrompt(
        self, events: List[Event], state: State, base_messages: List[Message]
    ) -> Message:
        """Create the prompt for condensation.
        This method is required by the CachingCondenser abstract base class.
        Args:
            events: The events to condense
            state: The current state
            base_messages: The messages that are already in the prompt (cached)
        Returns:
            The message with condensation instructions
        """
        nextMessageNumber = len(base_messages)

        # Create the condensation instructions
        condensation_instructions = f"""
I need you to condense our conversation history to make it more efficient. Please:

1. Identify which previous messages can be removed without losing important context
2. You have two options for condensing the conversation:

    Option A - Keep specific messages:
    For each message you decide to keep, respond with "KEEP: [message number]"

    Option B - Rewrite a range of messages:
    You can replace a sequence of messages with a single summary using:

    REWRITE [start-message-number] TO [end-message-number] WITH:
    [new-content]
    END-REWRITE

    This will replace all messages from start to end (inclusive) with a single message containing the new content.

3. Refer to messages by their number (0-{nextMessageNumber - 1})
4. You must keep at least one user message
5. Always keep the system prompt (message 0) if it exists

Respond ONLY with KEEP and REWRITE commands, nothing else.
"""
        # Create a message with the condensation instructions
        return Message(
            role='user',
            content=[TextContent(text=condensation_instructions)],
        )

    def processResponse(
        self, events: List[Event], state: State, response: Any, messages: List[Message]
    ) -> Union[Condensation, View]:
        """Process the LLM response to create a Condensation.
        This method is required by the CachingCondenser abstract base class.
        Args:
            events: The events that were condensed
            state: The current state
            response: The LLM response
        Returns:
            A Condensation or View object
        """
        # Parse the response to extract rewrite commands and keep indices
        rewrite_commands, keep_message_indices = self._parse_condensation_response(
            response
        )

        # Condense the events
        return self._condense_events(
            events, messages, rewrite_commands, keep_message_indices
        )

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

    def _contains_trigger_word(self, events: List[Event]) -> bool:
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

    def _parse_condensation_response(
        self, response: Any
    ) -> Tuple[List[RewriteCommand], List[int]]:
        # Parse the response to get the list of messages to keep and any REWRITE commands
        keep_message_indices = []
        rewrite_commands = []
        rewrite_start = None
        rewrite_end = None
        rewrite_content: List[str] = []

        response_text = response.choices[0].message.content or ''

        lines = response_text.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Process KEEP commands
            if line.startswith('KEEP:'):
                try:
                    index = int(line.replace('KEEP:', '').strip())
                    keep_message_indices.append(index)
                except ValueError:
                    pass
                i += 1

            # Process REWRITE commands
            elif line.startswith('REWRITE ') and ' TO ' in line and ' WITH:' in line:
                try:
                    # Extract the start and end event IDs from the line
                    command_parts = line.split(' WITH:')[0].strip()
                    range_parts = command_parts.replace('REWRITE ', '').split(' TO ')
                    rewrite_start = int(range_parts[0].strip())
                    rewrite_end = int(range_parts[1].strip())

                    # Collect content until END-REWRITE
                    rewrite_content = []
                    i += 1  # Move to the next line after the REWRITE command

                    while i < len(lines) and lines[i].strip() != 'END-REWRITE':
                        rewrite_content.append(lines[i])
                        i += 1

                    if i < len(lines) and lines[i].strip() == 'END-REWRITE':
                        # Found the end marker, create the rewrite command
                        rewrite_commands.append(
                            RewriteCommand(
                                start=rewrite_start,
                                end=rewrite_end,
                                content='\n'.join(rewrite_content),
                            )
                        )

                    # Skip the END-REWRITE line
                    i += 1

                except (ValueError, IndexError) as e:
                    logger.info(
                        f"Error parsing line '{line}': {e}. Skipping this line."
                    )
                    i += 1
            else:
                # Skip any other lines
                i += 1

        return rewrite_commands, keep_message_indices

    def _condense_events(
        self,
        events: List[Event],
        messages: List[Message],
        rewrite_commands: List[RewriteCommand],
        keep_message_indices: List[int],
    ) -> Union[Condensation, View]:
        """Condense events based on LLM's response.

        Args:
            events: The original list of events.
            messages: The list of messages derived from events.
            rewrite_commands: List of rewrite commands from the LLM.
            keep_message_indices: Indices of messages to keep.

        Returns:
            A Condensation or View object.
        """
        # If no indices or rewrite commands are provided, keep all events
        if not keep_message_indices and not rewrite_commands:
            return View.from_events(events)

        keep_events = []

        # Add events that were not sent to the LLM (i.e., events without a corresponding `_event` in messages)
        for event in events:
            if not any(message._event == event for message in messages):
                if event.id == Event.INVALID_ID:
                    raise ValueError(f'Event {event} had an invalid id.')
                keep_events.append(event)

        # Add the events to keep based on the LLM's response
        for index in keep_message_indices:
            try:
                message = messages[index]
                if message._event:
                    keep_events.append(message._event)
            except IndexError:
                pass

        # Check that there is at least one user message left
        if not any(event.source == EventSource.USER for event in keep_events):
            for event in events:
                if event.source == EventSource.USER:
                    keep_events.append(event)
                    break

        # Create a list of event IDs to forget
        forgotten_event_ids = [event.id for event in events if event not in keep_events]

        if rewrite_commands:
            summary = '\n'.join([rewrite.content for rewrite in rewrite_commands])
        else:
            summary = None

        # Create and return the condensation action
        return Condensation(
            action=CondensationAction(
                forgotten_event_ids=forgotten_event_ids, summary=summary
            )
        )


@dataclass
class RewriteCommand:
    """Represents a rewrite command parsed from the LLM response."""

    start: int
    end: int
    content: str
