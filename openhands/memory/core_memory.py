from openhands.memory.base_memory import Memory


class CoreMemory(Memory):
    """Memory contents to be inserted in the prompt. This includes key facts and context
    that the LLM needs to maintain about its current tasks and capabilities."""

    def __init__(self, limit: int = 1500):
        super().__init__()
        self.char_limit = limit
        self.blocks = {
            'personality': [],  # agent's personality traits and capabilities
            'task_context': [],  # important context about current tasks
        }

    def add_block(self, category: str, content: str) -> bool:
        """Add a memory block to a specific category.
        Returns True if successful, False if would exceed limit."""
        if category not in self.blocks:
            raise ValueError(
                f'Invalid category: {category}. Must be one of {list(self.blocks.keys())}'
            )

        # Calculate total size with new content
        potential_content = self.format_blocks() + f'\n- {content}'
        if len(potential_content) > self.char_limit:
            return False

        self.blocks[category].append(content)
        return True

    def get_blocks(
        self, category: str | None = None
    ) -> dict[str, list[str]] | list[str]:
        """Get memory blocks, optionally filtered by category."""
        if category:
            return self.blocks.get(category, [])
        return self.blocks

    def format_blocks(self) -> str:
        """Format memory blocks for inclusion in the system prompt."""
        formatted = []

        for category, items in self.blocks.items():
            if items:
                formatted.append(f"\n{category.replace('_', ' ').title()}:")
                formatted.extend([f'- {item}' for item in items])

        return '\n'.join(formatted)

    def __str__(self) -> str:
        return self.format_blocks()

    def to_dict(self) -> dict:
        return {category: items for category, items in self.blocks.items()}

    def reset(self) -> None:
        """Reset all memory blocks."""
        for category in self.blocks:
            self.blocks[category] = []
