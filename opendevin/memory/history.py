import opendevin.core.utils.json as json
from opendevin.core.exceptions import AgentEventTypeError
from opendevin.core.logger import opendevin_logger as logger


class ShortTermHistory:
    """
    The short term history is the most recent series of events.

    The short term history includes core events, which the agent learned in the initial prompt, and recent events of interest from the event stream.
    An agent can send this in the prompt or use it for other purpose.
    """

    def __init__(self):
        """
        Initialize the empty lists of events
        """
        self.recent_events = []
        # core events are events that the agent learned in the initial prompt
        self.core_events = []

    def add_event(self, event_dict: dict, core=False):
        """
        Adds an event to memory if it is a valid event.

        Parameters:
        - event_dict (dict): The event that we want to add to memory

        Raises:
        - AgentEventTypeError: If event_dict is not a dict
        """
        if not isinstance(event_dict, dict):
            raise AgentEventTypeError()

        # add to core events or to the list of other recent events
        if core:
            self.core_events.append(event_dict)
        else:
            self.recent_events.append(event_dict)

    def get_events(self):
        """
        Get the events in the agent's recent history, including core knowledge (the events it learned in the initial prompt).

        Returns:
        - List: The list of events that the agent remembers easily.
        """
        return self.recent_events + self.core_events

    def get_core_events(self):
        """
        Get the events in the agent's initial prompt.

        Returns:
        - List: The list of core events.
        """
        return self.core_events

    def get_recent_events(self, num_events=5):
        """
        Get the most recent events in the agent's short term history.

        Will not return core events.

        Parameters:
        - num_events (int): The number of recent events to return

        Returns:
        - List: The list of the most recent events.
        """
        return self.recent_events[-num_events:]

    def get_total_length(self):
        """
        Gives the total number of characters in all history

        Returns:
        - Int: Total number of characters of the recent history.
        """
        total_length = 0
        for t in self.recent_events:
            try:
                total_length += len(json.dumps(t))
            except TypeError as e:
                logger.error('Error serializing event: %s', str(e), exc_info=False)
        return total_length
