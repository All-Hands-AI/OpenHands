class StepCounter:
    """Automatically manages step numbering for settings flows."""

    def __init__(self, total_steps: int):
        self.current_step = 0
        self.total_steps = total_steps

    def next_step(self, prompt: str) -> str:
        """Get the next step prompt with automatic numbering."""
        self.current_step += 1
        return f'(Step {self.current_step}/{self.total_steps}) {prompt}'

    def existing_step(self, prompt: str) -> str:
        return f'(Step {self.current_step}/{self.total_steps}) {prompt}'
