from dataclasses import dataclass
from openhands.events.observation import Observation


@dataclass
class CostEvent(Observation):
    """Event emitted when a cost is incurred by the LLM."""
    step_cost: float
    total_cost: float
    description: str

    def __init__(self, step_cost: float, total_cost: float, description: str):
        super().__init__(content="")  # Content will be set in post_init
        self.step_cost = step_cost
        self.total_cost = total_cost
        self.description = description

    def __post_init__(self):
        super().__post_init__()
        self.observation = "cost"
        self.content = f"Cost: ${self.step_cost:.4f} (Total: ${self.total_cost:.4f}) - {self.description}"
