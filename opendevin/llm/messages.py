class Message:
    """
    A class that stores the content of an Action or Observation Class.
    It also lets the agent know if the content is condensable.
    """

    message: dict[str, str]
    condensable: bool
    event_id: int

    def __init__(self, message, condensable=True, event_id=-1):
        self.message = message
        self.condensable = condensable
        self.event_id = event_id
