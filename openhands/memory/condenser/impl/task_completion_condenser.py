from __future__ import annotations

from typing import List, Set, Tuple

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
        self.condensed_chunks: Set[Tuple[int, int]] = (
            set()
        )  # Track which chunks have been condensed
        self.highest_processed_id = -1  # Track highest event ID we've processed
        super().__init__()

    def _is_important_event(self, event: Event) -> bool:
        """Check if an event should be kept in the history.

        Args:
            event: The event to check

        Returns:
            bool: True if the event should be kept, False otherwise
        """
        # Keep user messages
        if (
            event.source == EventSource.USER
            and hasattr(event, 'action')
            and event.action == ActionType.MESSAGE
        ):
            return True

        # Keep edit observations with file text (report files)
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

        # Keep finish actions with file text (conclusions)
        if (
            event.source == EventSource.AGENT
            and hasattr(event, 'action')
            and event.action == ActionType.MESSAGE
        ):
            return True

        return False

    def _find_task_chunks(self, view: View) -> List[Tuple[int, int]]:
        """Find chunks of completed tasks in the view.

        Each task starts with a user message and ends right before the next user message.
        Does NOT include the last incomplete chunk if it's still ongoing (no next user message yet).
        Only considers events with IDs higher than the last processed ID.

        Args:
            view: The view to analyze

        Returns:
            List of tuples (start_index, end_index) for each task chunk
        """
        task_chunks = []
        user_message_indices = []

        # Track if we've found new events
        found_new_events = False

        # First identify all user message indices for events we haven't processed yet
        for i, event in enumerate(view):
            # Skip events with negative IDs or None source (likely condensation events)
            if event.id < 0 or event.source is None:
                continue

            # Skip events we've already processed
            if event.id <= self.highest_processed_id:
                continue

            # We've found at least one new event
            found_new_events = True

            if (
                event.source == EventSource.USER
                and hasattr(event, 'action')
                and event.action == ActionType.MESSAGE
            ):
                user_message_indices.append(i)
                logger.info(
                    f'[TaskCompletionCondenser]: New user message found at index {i}, ID: {event.id}'
                )

        # If we don't have new user messages, return empty list
        if not found_new_events or len(user_message_indices) < 2:
            logger.info('[TaskCompletionCondenser]: No new user message chunks found')
            return []

        # Create chunks between consecutive user messages
        for i in range(len(user_message_indices) - 1):
            start_idx = user_message_indices[i]
            end_idx = (
                user_message_indices[i + 1] - 1
            )  # End before the next user message
            task_chunks.append((start_idx, end_idx))

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
        # Find all new completed task chunks
        task_chunks = self._find_task_chunks(view)

        # Collect IDs of events to forget
        forgotten_event_ids = []
        new_highest_id = self.highest_processed_id

        # Process each task chunk
        for start_idx, end_idx in task_chunks:
            chunk_events = view[start_idx : end_idx + 1]

            # Log the chunk we're processing
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
        # """Entry point for condensation.

        # If there are completed task chunks that need condensing, perform the condensation.
        # Otherwise, return the original view.
        # """
        # logger.info(f'[TaskCompletionCondenser]: condense view={view}')

        # if self.should_condense(view):
        #     return self.get_condensation(view)
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
        logger.info(
            f'[TaskCompletionCondenser]: should_condense called with view length={len(view)}'
        )
        logger.info(
            f'[TaskCompletionCondenser]: Current highest_processed_id={self.highest_processed_id}'
        )

        # Check if we have any new events to process
        has_new_events = False
        for event in view:
            if event.id > self.highest_processed_id and event.id >= 0:
                has_new_events = True
                break

        if not has_new_events:
            logger.info('[TaskCompletionCondenser]: No new events to process')
            return False

        # Log event stream for debugging (only new events)
        logger.info('[TaskCompletionCondenser]: --- New events snapshot ---')
        new_event_count = 0
        for i, event in enumerate(view):
            # Skip events we've already processed or condensation events
            if (
                event.id <= self.highest_processed_id
                or event.id < 0
                or event.source is None
            ):
                continue

            new_event_count += 1
            event_id = getattr(event, 'id', 'unknown')
            event_source = getattr(event, 'source', 'unknown')
            event_action = getattr(event, 'action', 'N/A')
            logger.info(
                f'[TaskCompletionCondenser]: Event {i} - ID:{event_id}, Source:{event_source}, Action:{event_action}'
            )
        logger.info(
            f'[TaskCompletionCondenser]: --- End of new events snapshot ({new_event_count} new events) ---'
        )

        # Find new task chunks using the existing method (will only consider new events)
        task_chunks = self._find_task_chunks(view)

        result = len(task_chunks) > 0
        logger.info(
            f'[TaskCompletionCondenser]: should_condense result={result} with {len(task_chunks)} new chunks'
        )
        return result


# Register the configuration type
TaskCompletionCondenser.register_config(TaskCompletionCondenserConfig)
