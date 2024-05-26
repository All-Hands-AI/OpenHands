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
        # we're not making an obs just yet
        # observation = event[1]
        if isinstance(action, AgentSummarizeAction):
            self.replace_events_with_summary(action)
        else:
            super().append(event)

    def replace_events_with_summary(self, summary_action: AgentSummarizeAction):
        start_id = None
        end_id = None

        for i, event in enumerate(self):
            if event[0].id == summary_action._chunk_start:
                start_id = i
            if event[1].id == summary_action._chunk_end:
                end_id = i
                break

        if start_id is not None and end_id is not None:
            # create the SummaryObservation based on the AgentSummarizeAction
            summary_observation = SummaryObservation(content=summary_action.summary)

            # clean up the action if we're doing it this way, this is odd
            summary_action.summary = ''

            # replace the events in the specified range with the summary action and observation
            self[start_id:end_id] = [(summary_action, summary_observation)]

        # we didn't have the chunk, just return
