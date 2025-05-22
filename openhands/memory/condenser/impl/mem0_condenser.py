# from __future__ import annotations

# import asyncio
# from typing import Any, Optional

# from openhands.core.config.condenser_config import Mem0CondenserConfig
# from openhands.core.logger import openhands_logger as logger
# from openhands.events.action import AgentFinishAction
# from openhands.memory.condenser.condenser import Condensation, RollingCondenser, View


# class Mem0Condenser(RollingCondenser):
#     """A condenser that removes events that have already been synchronized to Mem0.

#     This condenser tracks the last time the conversation was synchronized with Mem0
#     and removes events before that timestamp, keeping only the most recent events
#     that haven't been synchronized yet. It ensures:

#     1. The initial user message (task) is always preserved
#     2. Important context related to the conversation is maintained
#     3. Events that have already been synchronized to Mem0 are removed
#     4. New events since the last synchronization are kept

#     This approach drastically reduces context window usage while ensuring
#     all important knowledge is preserved in the Mem0 knowledge base.
#     """

#     def __init__(self, keep_first: int = 1):
#         """Initialize the Mem0Condenser.

#         Args:
#             keep_first: Number of initial events to always keep (typically the user's task)
#         """
#         self.keep_first = keep_first
#         self._last_sync_timestamp: Optional[float] = None
#         self._last_task_completion_index: Optional[int] = None

#         super().__init__()

#     async def _fetch_last_sync_timestamp(self) -> Optional[float]:
#         """Get the last sync timestamp from Mem0.

#         Returns:
#             The timestamp of the last synchronization or None if not available
#         """
#         try:
#             last_sync_timestamp = await get_last_sync_timestamp()

#             logger.info(f'Last sync timestamp: {last_sync_timestamp}')

#             if last_sync_timestamp is not None:
#                 self._last_sync_timestamp = last_sync_timestamp
#             return last_sync_timestamp
#         except Exception as e:
#             logger.warning(f'Failed to get last sync timestamp from Mem0: {e}')
#             return None

#     def should_condense(self, view: View) -> bool:
#         """Determine if the view should be condensed.

#         The view should be condensed if:
#         1. We have a valid last sync timestamp
#         2. There is an AgentFinishAction in the view (indicating task completion)
#         3. The task completion is after our last known task completion

#         Args:
#             view: The view to check

#         Returns:
#             True if the view should be condensed, False otherwise
#         """
#         # Run the async function to get the timestamp in a synchronous context
#         if self._last_sync_timestamp is None:
#             try:
#                 self._last_sync_timestamp = asyncio.get_event_loop().run_until_complete(
#                     self._fetch_last_sync_timestamp()
#                 )
#             except Exception:
#                 # If we can't get the timestamp, don't condense
#                 return False

#         # Don't condense if we don't have a valid last sync timestamp
#         if self._last_sync_timestamp is None:
#             logger.warning(
#                 'Mem0Condenser: Last sync timestamp is None, using fallback strategy'
#             )
#             return False

#         # Find the latest task completion in the view
#         latest_task_completion = None
#         for i, event in enumerate(view):
#             if isinstance(event, AgentFinishAction):
#                 latest_task_completion = i

#         # Don't condense if there's no task completion
#         if latest_task_completion is None:
#             return False

#         # Don't condense if we've already condensed up to this task completion
#         if (
#             self._last_task_completion_index is not None
#             and latest_task_completion <= self._last_task_completion_index
#         ):
#             return False

#         # Update the last task completion index
#         self._last_task_completion_index = latest_task_completion
#         return True

#     def _get_event_timestamp(self, event: Any) -> Optional[float]:
#         """Safely extract timestamp from an event, ensuring it's a float.

#         Args:
#             event: The event to extract timestamp from

#         Returns:
#             A float timestamp or None if not available
#         """
#         if not hasattr(event, 'timestamp'):
#             return None

#         timestamp = event.timestamp
#         # Convert timestamp to float if it's a string or another convertible type
#         if timestamp is not None and not isinstance(timestamp, float):
#             try:
#                 return float(timestamp)
#             except (ValueError, TypeError):
#                 return None

#         return timestamp

#     def get_condensation(self, view: View) -> Condensation:
#         """Create a condensation action that will remove events before the last sync timestamp.

#         This is called when should_condense() returns True.

#         Args:
#             view: The view to condense

#         Returns:
#             A Condensation containing an action that will be added to the event stream
#         """
#         # Get events to keep - always include the first keep_first events (typically task description)
#         head = view[: self.keep_first]

#         # We should always have a valid last_sync_timestamp at this point due to the checks in should_condense
#         # But add a safety check just in case
#         if self._last_sync_timestamp is None:
#             logger.warning(
#                 'Mem0Condenser: Last sync timestamp is None, using fallback strategy'
#             )
#             # Skip to fallback strategy
#         else:
#             # Find the first event after the last sync timestamp
#             sync_index = self.keep_first
#             for i in range(self.keep_first, len(view)):
#                 event_timestamp = self._get_event_timestamp(view[i])

#                 # Skip events without a valid timestamp
#                 if event_timestamp is None:
#                     continue

#                 # Only keep events that happened after the last sync timestamp
#                 # Safe comparison: both are now guaranteed to be float
#                 if event_timestamp > self._last_sync_timestamp:
#                     sync_index = i
#                     break

#             # Calculate the indices of events to forget
#             if sync_index > self.keep_first:
#                 first_forgotten = self.keep_first
#                 last_forgotten = sync_index - 1
#                 tail = view[sync_index:]

#                 # Record metadata about this condensation
#                 self.add_metadata('mem0_sync_timestamp', self._last_sync_timestamp)
#                 self.add_metadata(
#                     'forgotten_events_count', last_forgotten - first_forgotten + 1
#                 )
#                 self.add_metadata('kept_events_count', len(head) + len(tail))
#                 self.add_metadata(
#                     'task_completion_index', self._last_task_completion_index
#                 )

#                 logger.info(
#                     f'Mem0Condenser: Removing {last_forgotten - first_forgotten + 1} events '
#                     f'between indices {first_forgotten} and {last_forgotten} '
#                     f'that were synchronized before timestamp {self._last_sync_timestamp}'
#                 )

#                 return Condensation(
#                     action=view.condensation_action(
#                         forgotten_events_start_id=view[first_forgotten].id,
#                         forgotten_events_end_id=view[last_forgotten].id,
#                     )
#                 )

#         # If we didn't find events to remove or couldn't use timestamp-based approach, use fallback
#         logger.warning(
#             'Mem0Condenser: No events found to remove based on timestamp. '
#             'Using recent events fallback strategy.'
#         )

#         # Fallback to keeping only the head and events after the last task completion
#         if self._last_task_completion_index is not None:
#             tail = view[self._last_task_completion_index + 1 :]
#             first_forgotten = len(head)
#             last_forgotten = self._last_task_completion_index

#             self.add_metadata('fallback_strategy', 'task_completion')
#             self.add_metadata(
#                 'forgotten_events_count', last_forgotten - first_forgotten + 1
#             )
#             self.add_metadata('kept_events_count', len(head) + len(tail))
#             self.add_metadata('task_completion_index', self._last_task_completion_index)

#             return Condensation(
#                 action=view.condensation_action(
#                     forgotten_events_start_id=view[first_forgotten].id,
#                     forgotten_events_end_id=view[last_forgotten].id,
#                 )
#             )

#         # If we can't condense, just return the current view
#         return Condensation(
#             action=view.condensation_action(
#                 forgotten_events_start_id=0,
#                 forgotten_events_end_id=0,
#             )
#         )

#     def condense(self, view: View) -> View | Condensation:
#         """Entry point for condensation."""
#         # Let RollingCondenser's implementation handle the actual logic
#         return super().condense(view)

#     @classmethod
#     def from_config(cls, config: Mem0CondenserConfig) -> Mem0Condenser:
#         """Create a Mem0Condenser from a configuration."""
#         return Mem0Condenser(**config.model_dump(exclude=['type']))


# # Register the configuration type
# Mem0Condenser.register_config(Mem0CondenserConfig)
