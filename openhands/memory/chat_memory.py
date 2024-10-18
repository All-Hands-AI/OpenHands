from .base_memory import Memory


class ChatMemory(Memory):
    """Manages conversational context like persona and user details."""

    def __init__(self, persona: str, human: str, limit: int = 2000):
        self.persona = persona
        self.human = human
        self.limit = limit

    def to_dict(self) -> dict:
        return {
            'persona': self.persona,
            'human': self.human,
            'limit': self.limit,
        }

    def from_dict(self, data: dict) -> None:
        self.persona = data.get('persona', '')
        self.human = data.get('human', '')
        self.limit = data.get('limit', 2000)

    def __str__(self) -> str:
        return f'Persona: {self.persona}\nHuman: {self.human}'
