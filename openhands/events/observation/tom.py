"""Tom-related observation types for OpenHands."""

from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class ConsultTomAgentObservation(Observation):
    """Observation containing Tom agent consultation result."""

    content: str = ''
    observation: str = ObservationType.CONSULT_TOM_AGENT
