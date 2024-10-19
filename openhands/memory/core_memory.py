from openhands.memory.base_memory import Memory


class CoreMemory(Memory):
    """Memory contents to be inserted in the prompt. This includes summaries and other information that the LLM thought was important."""

    memory_blocks: list[str]

    def __init__(self, limit: int = 1500):
        super().__init__()
        self.limit = limit
        self.memory_blocks = []

    def to_dict(self) -> dict:
        return {
            'limit': self.limit,
        }

    def from_dict(self, data: dict) -> None:
        self.limit = data.get('limit', 1500)

    def __str__(self) -> str:
        return (
            f'CoreMemory: {{limit: {self.limit}, memory_block: {self.memory_blocks}}}'
        )

    def reset(self) -> None:
        self.memory_blocks = []
