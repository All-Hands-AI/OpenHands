from openhands.memory.base_memory import Memory


class CoreMemory(Memory):
    """Holds essential system messages and foundational context."""

    def __init__(self, system_message: str, limit: int = 1500):
        self.system_message = system_message
        self.limit = limit

    def to_dict(self) -> dict:
        return {
            'system_message': self.system_message,
            'limit': self.limit,
        }

    def from_dict(self, data: dict) -> None:
        self.system_message = data.get('system_message', '')
        self.limit = data.get('limit', 1500)

    def __str__(self) -> str:
        return f'System Message: {self.system_message}'
