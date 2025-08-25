"""Tom-related observation types for OpenHands."""

from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class ImproveInstructionObservation(Observation):
    """Observation containing fake user message to trigger Tom improve instruction."""

    content: str = ''
    observation: str = ObservationType.IMPROVE_INSTRUCTION
