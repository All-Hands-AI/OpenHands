from openhands.events.observation.observation import Observation


class TimeoutObservation(Observation):
    """Observation returned when an action times out but should not be treated as a fatal error."""

    observation = 'timeout'

    def __init__(self, message: str):
        super().__init__(content=message)

    def __str__(self) -> str:
        return f'[Timeout] {self.content}'
