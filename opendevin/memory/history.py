import opendevin.core.utils.json as json
from opendevin.core.exceptions import AgentEventTypeError
from opendevin.core.logger import opendevin_logger as logger


class ShortTermHistory:
    """
    The short term history is the most recent series of events.
    An agent can send this in the prompt or use it for other purpose.
    """

    def __init__(self):
        """
        Initialize the empty list of events
        """
        self.events = []

    def add_event(self, event_dict: dict):
        """
        Adds an event to memory if it is a valid event.

        Parameters:
        - event_dict (dict): The event that we want to add to memory

        Raises:
        - AgentEventTypeError: If event_dict is not a dict
        """
        if not isinstance(event_dict, dict):
            raise AgentEventTypeError()
        self.events.append(event_dict)

    def get_events(self):
        """
        Get the events in the agent's recent history.

        Returns:
        - List: The list of events that the agent remembers easily.
        """
        return self.events

    def get_total_length(self):
        """
        Gives the total number of characters in all history

        Returns:
        - Int: Total number of characters of the recent history.
        """
        total_length = 0
        for t in self.events:
            try:
                total_length += len(json.dumps(t))
            except TypeError as e:
                logger.error('Error serializing event: %s', str(e), exc_info=False)
        return total_length
