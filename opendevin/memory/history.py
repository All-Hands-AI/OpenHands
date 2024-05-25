from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.action import Action
from opendevin.events.action.agent import AgentSummarizeAction
from opendevin.events.observation.observation import Observation
from opendevin.events.observation.summary import SummaryObservation


class ShortTermHistory(list[tuple[Action, Observation]]):
    """
    A list of events that represents the short-term memory of the agent.
    """

    def append(self, event):
        """
        Append an event to the history.

        Args:
            event: The event to append.
        """
        if not isinstance(event, tuple):
            raise TypeError(f'Event must be a tuple, got {type(event)}')

        action = event[0]
        observation = event[1]
        if isinstance(action, AgentSummarizeAction) or isinstance(
            observation, SummaryObservation
        ):
            self.replace_chunk_with_summary(
                action._chunk_start, action._chunk_end, action, observation
            )
        else:
            super().append(event)

    def replace_chunk_with_summary(
        self,
        start_id: int,
        end_id: int,
        summary_action: AgentSummarizeAction,
        summary_observation: SummaryObservation,
    ):
        """
        Replace a chunk of events determined by start_id and end_id with the summary events.

        Args:
            start_id: The ID of the first event in the chunk to be replaced.
            end_id: The ID of the last event in the chunk to be replaced.
            summary_action: The summary action event to replace the chunk.
            summary_observation: The summary observation event to replace the chunk.

        Returns:
            The updated ShortTermHistory.
        """
        chunk_start = None
        chunk_end = None

        for i, event in enumerate(self):
            if event[0].id == start_id:
                chunk_start = i
            if event[1].id == end_id:
                chunk_end = i
                break

        if chunk_start is not None and chunk_end is not None:
            logger.debug(
                f'Replacing chunk from {chunk_start} to {chunk_end} with summary'
            )
            self[chunk_start : chunk_end + 1] = [(summary_action, summary_observation)]

        # we didn't have the chunk, just return
