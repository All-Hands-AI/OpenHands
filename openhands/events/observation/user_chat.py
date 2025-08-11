from dataclasses import dataclass

from .observation import Observation


@dataclass
class UserChatObservation(Observation):
    """
    This observation is sent when the user sends a message to the AI chat.
    """

    observation: str = 'chat'

    @property
    def message(self) -> str:
        return 'AI chat response.'
