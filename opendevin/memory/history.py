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
        start_id = summary_action._chunk_start
        end_id = summary_action._chunk_end

        # valid start and end indices for the chunk
        if start_id == -1 or end_id == -1 or start_id > end_id or end_id > len(self):
            # weird, but just return
            return

        # create the SummaryObservation based on the AgentSummarizeAction
        summary_observation = SummaryObservation(content=summary_action.summary)

        # clean up the action if we're doing it this way, this is odd
        summary_action.summary = ''

        # replace the events in the specified range with the summary action and observation
        self[start_id:end_id] = [(summary_action, summary_observation)]
