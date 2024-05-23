from dataclasses import dataclass

from opendevin.core.schema.observation import ObservationType
from opendevin.events.observation.observation import Observation


@dataclass
class SummaryObservation(Observation):
    """Represents a summary observation of multiple agent actions."""

    priority: str | None = None
    observation: str = ObservationType.SUMMARY

    def to_dict(self) -> dict:
        """Convert the SummaryObservation instance to a dictionary."""
        return {
            'observation': self.observation,
            'content': self.content,
            'priority': self.priority,
        }
