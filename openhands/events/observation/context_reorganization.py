from dataclasses import dataclass, field
from typing import Dict, List

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class ContextReorganizationObservation(Observation):
    """The output of a context reorganization action.

    This observation contains a structured summary of the conversation and
    a list of important files from the workspace.
    """

    summary: str
    files: List[Dict] = field(default_factory=list)
    observation: str = ObservationType.CONTEXT_REORGANIZATION

    @property
    def message(self) -> str:
        file_paths = (
            ', '.join([f['path'] for f in self.files]) if self.files else 'no files'
        )
        return f'Context reorganized with summary and files: {file_paths}'
