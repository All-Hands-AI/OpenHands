from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from openhands.controller.state.state import State
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.core.schema.action import ActionType
from openhands.events.action.agent import CondensationAction
from openhands.events.event import Event, EventSource
from openhands.memory.condenser.condenser import Condensation, Condenser, View

if TYPE_CHECKING:
    from openhands.agenthub.llm_cache_code_agent.llm_cache_code_agent import (
        LLMCacheCodeAgent,
    )


class LLMAgentCacheCondenser(Condenser):
    """A condenser that is tightly coupled with an agent to take advantage of LLM caching.

    This condenser is designed to be used with LLMCacheCodeAgent. It ensures that the LLM
    instance used by the condenser is the same as the one used by the agent, allowing for
    effective caching of prompts.

    Instead of creating a separate prompt for condensation, this condenser uses the same
    prompt format as the agent and appends condensation instructions at the end. This allows
    the LLM to take advantage of the cached prompt and only process the new instructions.
    """

    def __init__(self, agent: LLMCacheCodeAgent, max_size: int = 100):
        """Initialize the condenser with the agent instance.

        Args:
            agent: The agent instance. This is used to access the LLM, conversation memory,
                  and prompt manager, ensuring that caching works properly.
            max_size: The maximum number of events to keep before condensing.
        """
        self.agent = agent
        self.llm = agent.llm
        self.conversation_memory = agent.conversation_memory
        self.prompt_manager = agent.prompt_manager
        self.max_size = max_size

        # Verify that the LLM supports caching
        if not self.llm.is_caching_prompt_active():
            # Raise an exception since this is an experimental feature
            # and we need caching to be enabled for it to work properly
            raise ValueError(
                'LLMAgentCacheCondenser: The LLM does not support prompt caching. '
                'This condenser requires prompt caching to be enabled.'
            )

        super().__init__()

    def condensed_history(self, state: State) -> View | Condensation:
        """Condense the state's history using the agent's LLM.

        This overrides the base method to pass the state to condense.

        Args:
            state: The current state.

        Returns:
            A View or Condensation object.
        """
        with self.metadata_batch(state):
            return self.condenseWithState(state)

    def containsTriggerWord(self, events: List[Event]) -> bool:
        """Check if the most recent user message contains the CONDENSE! trigger word.

        Args:
            events: The events to check.

        Returns:
            True if the most recent user message contains the trigger word, False otherwise.
        """
        if not events or len(events) < 2:  # Need at least 2 events to condense
            return False

        CONDENSATION_TRIGGER_WORD = 'CONDENSE!'

        # Iterate through events in reverse order to find the last user message
        for event in reversed(events):
            if (
                hasattr(event, 'source')
                and event.source == EventSource.USER
                and hasattr(event, 'action')
                and event.action == ActionType.MESSAGE
                and event.message is not None
            ):
                return CONDENSATION_TRIGGER_WORD in event.message

            # If we did a condensation, stop looking.
            if hasattr(event, 'action') and event.action == ActionType.CONDENSATION:
                return False

        return False

    def should_condense(self, events: List[Event]) -> bool:
        """Determine if the events should be condensed.

        Condensation is triggered in two cases:
        1. When the number of events exceeds max_size
        2. When the last event is from the user and contains the text "CONDENSE!"

        Args:
            events: The events to check.

        Returns:
            True if the events should be condensed, False otherwise.
        """
        # Check if the number of events exceeds max_size
        if len(events) > self.max_size:
            logger.info(f'Condensing events due to max size({self.max_size}) limit.')
            return True

        # Check if any recent user message contains "CONDENSE!"
        if self.containsTriggerWord(events):
            logger.info("Condensing events due to trigger word 'CONDENSE!'.")
            return True

        return False

    def condense(self, events: List[Event]):
        raise NotImplementedError(
            'LLMAgentCacheCondenser: This method should not be called directly. '
            + 'Use condense(events, state) instead.'
        )

    def condenseWithState(self, state: State) -> View | Condensation:
        """Condense the events using the agent's LLM.

        This implementation uses the agent's LLM to condense the events in a way that
        takes advantage of prompt caching. It formats the messages in the same way as
        the agent, but adds condensation instructions at the end.

        Args:
            state: The current state, used for LLM metadata.

        Returns:
            The condensed events, a View, or a Condensation.
        """
        view = View.from_events(state.history)
        if self.should_condense(state.history):
            return self._do_condensation(view.events, state)

        return view

    def _do_condensation(
        self, events: List[Event], state: State
    ) -> Condensation | View:
        """Do a condensation for the given events.

        Args:
            events: The events to condense.
            state: The current state, used for LLM metadata.

        Returns:
            A Condensation or View object based on the condensation process.
        """
        # Double-check that we have the required dependencies
        if not self.conversation_memory or not self.prompt_manager:
            raise ValueError(
                'LLMAgentCacheCondenser: Missing conversation_memory or prompt_manager. '
                'These are required for the condenser to work properly.'
            )

        messages = self._build_messages_for_condensation(events)

        # Use the agent's build_llm_completion_params to ensure consistent caching
        params = self.agent.build_llm_completion_params(messages, state)
        response = self.agent.llm.completion(**params)
        self.add_metadata('response', response.model_dump())

        rewrite_commands, keep_message_indices = self._parse_condensation_response(
            response
        )
        condensation = self._condense_events(
            events, messages, rewrite_commands, keep_message_indices
        )
        return condensation

    def _build_messages_for_condensation(self, events: List[Event]) -> list[Message]:
        # Process the events into messages using the same format as the agent
        # This ensures we can take advantage of the LLM's cache
        messages = self.agent._get_messages(events)

        nextMessageNumber = len(messages)

        # Add the condensation instructions as a user message at the end
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

3. Refer to the messages by their number.
    The first message, the system, prompt has number 0.
    The next is 1 and so on.
    All the way to the last message, this one, whose number is {nextMessageNumber}.

4. You can use both options together. For example:
    KEEP: 5
    KEEP: 8
    REWRITE 10 TO 15 WITH:
    User asked about database schema and agent explained the tables and relationships.
    END-REWRITE
    KEEP: 18

5. Focus on keeping messages that contain:
    - User requirements and constraints
    - Important code changes and decisions
    - Key error messages and debugging information
    - Critical context needed for the current task

6. You can remove or rewrite messages that:
    - Contain redundant information
    - Show intermediate steps that are no longer relevant
    - Contain verbose output that has already been processed

Please respond ONLY with KEEP and REWRITE commands as described above.
Do not include any other text in your response.
"""

        # Add the condensation instructions as the last message
        messages.append(
            Message(role='user', content=[TextContent(text=condensation_instructions)])
        )

        return messages

    def _parse_condensation_response(
        self, response: Message
    ) -> tuple[list[RewriteCommand], list[int]]:
        # Parse the response to get the list of messages to keep and any REWRITE commands
        keep_message_indices = []
        rewrite_commands = []
        rewrite_start = None
        rewrite_end = None
        rewrite_content: list[str] = []

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
        rewrite_commands: list[RewriteCommand],
        keep_message_indices: list[int],
    ) -> Condensation | View:
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
