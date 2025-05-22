from __future__ import annotations

from typing import List, Tuple

from openhands.core.config.condenser_config import TaskCompletionCondenserConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import ObservationType
from openhands.core.schema.action import ActionType
from openhands.events.action.agent import CondensationAction
from openhands.events.event import Event, EventSource
from openhands.memory.condenser.condenser import Condensation, RollingCondenser, View


class TaskCompletionCondenser(RollingCondenser):
    """A condenser that keeps only essential events for completed tasks.

    This condenser:
    1. Keeps the initial user message (task description)
    2. Keeps report markdown files (from edit observations with file text)
    3. Keeps final conclusions (from finish actions with file text)
    4. Condenses all other events
    """

    def __init__(self, keep_first: int = 1):
        """Initialize the TaskCompletionCondenser.

        Args:
            keep_first: Number of initial events to always keep (typically the user's task)
        """
        logger.info(
            f'[TaskCompletionCondenser]: Initialize successfully keep_first={keep_first}'
        )
        self.keep_first = keep_first
        self.highest_processed_id = -1
        super().__init__()

    def _is_important_event(self, event: Event) -> bool:
        """Check if an event should be kept in the history.

        Args:
            event: The event to check

        Returns:
            bool: True if the event should be kept, False otherwise
        """
        if (
            event.source == EventSource.USER
            and hasattr(event, 'action')
            and event.action == ActionType.MESSAGE
        ):
            return True

        if (
            event.source == EventSource.AGENT
            and hasattr(event, 'observation')
            and event.observation == ObservationType.EDIT  # file edit observation
        ):
            return True

        if (
            event.source == EventSource.AGENT
            and hasattr(event, 'action')
            and event.action == ActionType.EDIT
        ):
            return True

        if (
            event.source == EventSource.AGENT
            and hasattr(event, 'action')
            and event.action == ActionType.MESSAGE
        ):
            return True

        return False

    def _find_task_chunks(self, view: View) -> List[Tuple[int, int]]:
        """Find chunks of completed tasks in the view.

        Each task starts with a user message and ends with an agent message.
        Only considers events with IDs higher than the last processed ID.
        A valid chunk is from a user message to the next agent message (inclusive).

        Args:
            view: The view to analyze

        Returns:
            List of tuples (start_index, end_index) for each task chunk
        """
        task_chunks = []

        found_new_events = False

        # Process each event to find user messages and their corresponding agent responses
        i = 0
        while i < len(view):
            event = view[i]

            if event.id < 0 or event.source is None:
                i += 1
                continue

            if event.id <= self.highest_processed_id:
                i += 1
                continue

            found_new_events = True

            if (
                event.source == EventSource.USER
                and hasattr(event, 'action')
                and event.action == ActionType.MESSAGE
            ):
                start_idx = i
                logger.info(
                    f'[TaskCompletionCondenser]: Potential chunk start found at index {i}, ID: {event.id}'
                )

                # Look for the next agent message
                found_agent_message = False
                for j in range(i + 1, len(view)):
                    next_event = view[j]

                    # Skip events with negative IDs or None source
                    if next_event.id < 0 or next_event.source is None:
                        continue

                    if (
                        next_event.source == EventSource.AGENT
                        and hasattr(next_event, 'action')
                        and next_event.action == ActionType.MESSAGE
                    ):
                        # Found an agent message, create a chunk
                        end_idx = j  # Include the agent message in the chunk
                        task_chunks.append((start_idx, end_idx))
                        logger.info(
                            f'[TaskCompletionCondenser]: Created chunk from index {start_idx} to {end_idx}'
                        )
                        found_agent_message = True
                        break

                if not found_agent_message:
                    logger.info(
                        f'[TaskCompletionCondenser]: No agent message found after user message at index {i}'
                    )

            i += 1

        # If we don't have new events or no chunks were created, return empty list
        if not found_new_events or not task_chunks:
            logger.info('[TaskCompletionCondenser]: No new task chunks found')
            return []

        logger.info(
            f'[TaskCompletionCondenser]: Found {len(task_chunks)} new task chunks'
        )
        logger.info(f'[TaskCompletionCondenser]: task_chunks={task_chunks}')

        return task_chunks

    def get_condensation(self, view: View) -> Condensation:
        """Create a condensation action that will keep only essential events.

        This is called when should_condense() returns True.

        Args:
            view: The view to condense

        Returns:
            A Condensation containing an action that will be added to the event stream
        """
        task_chunks = self._find_task_chunks(view)

        forgotten_event_ids = []
        new_highest_id = self.highest_processed_id

        # Process each task chunk
        for start_idx, end_idx in task_chunks:
            chunk_events = view[start_idx : end_idx + 1]

            logger.info(
                f'[TaskCompletionCondenser]: Processing chunk {start_idx}-{end_idx} with {len(chunk_events)} events'
            )

            # First event in the chunk is always the user message, which we keep
            # For all other events, check if they're important
            for i, event in enumerate(chunk_events):
                # Skip events with negative IDs (likely condensation events)
                if event.id < 0:
                    continue

                # Update highest processed ID
                new_highest_id = max(new_highest_id, event.id)

                if i == 0:  # First event is user message, always keep it
                    continue

                if not self._is_important_event(event):
                    forgotten_event_ids.append(event.id)

        # Update our highest processed ID
        self.highest_processed_id = new_highest_id
        logger.info(
            f'[TaskCompletionCondenser]: Updated highest processed ID to {self.highest_processed_id}'
        )

        # Record metadata about this condensation
        self.add_metadata('forgotten_events_count', len(forgotten_event_ids))
        self.add_metadata('kept_events_count', len(view) - len(forgotten_event_ids))
        self.add_metadata('task_chunks', len(task_chunks))
        self.add_metadata('highest_processed_id', self.highest_processed_id)

        logger.info(
            f'[TaskCompletionCondenser]: get_condensation forgotten_event_ids={forgotten_event_ids}'
        )

        return Condensation(
            action=CondensationAction(
                forgotten_event_ids=forgotten_event_ids,
                summary=None,
                summary_offset=None,
            )
        )

    def condense(self, view: View) -> View | Condensation:
        """Entry point for condensation.

        If there are completed task chunks that need condensing, perform the condensation.
        Otherwise, return the original view.
        """
        return super().condense(view)

    @classmethod
    def from_config(
        cls, config: TaskCompletionCondenserConfig
    ) -> TaskCompletionCondenser:
        """Create a TaskCompletionCondenser from a configuration."""
        return TaskCompletionCondenser(**config.model_dump(exclude=['type']))

    def should_condense(self, view: View) -> bool:
        """Determine if the view should be condensed.

        The view should be condensed if there are new completed task chunks
        (user message followed by another user message) that haven't been processed yet.

        Args:
            view: The view to check

        Returns:
            True if the view should be condensed, False otherwise
        """

        has_new_events = False
        for event in view:
            if event.id > self.highest_processed_id and event.id >= 0:
                has_new_events = True
                break

        if not has_new_events:
            logger.info('[TaskCompletionCondenser]: No new events to process')
            return False

        task_chunks = self._find_task_chunks(view)

        result = len(task_chunks) > 0
        logger.info(
            f'[TaskCompletionCondenser]: should_condense result={result} with {len(task_chunks)} new chunks'
        )
        return result


# Register the configuration type
TaskCompletionCondenser.register_config(TaskCompletionCondenserConfig)
