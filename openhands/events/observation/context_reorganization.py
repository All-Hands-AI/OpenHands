from dataclasses import dataclass, field
from typing import Dict, List

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class ContextReorganizationObservation(Observation):
    """The output of a context reorganization action.

    This observation contains a structured summary of the conversation and
    a list of important files from the workspace.

    The files field is a list of dictionaries, where each dictionary contains:
    - 'path': The path to the file (required)
    - 'view_range': Optional tuple of (start_line, end_line) to specify a range of lines
    """

    summary: str
    files: List[Dict[str, object]] = field(default_factory=list)
    observation: str = ObservationType.CONTEXT_REORGANIZATION

    @property
    def message(self) -> str:
        file_paths = (
            ', '.join(
                [str(f['path']) if isinstance(f, dict) else str(f) for f in self.files]
            )
            if self.files
            else 'no files'
        )
        return f'Context reorganized with summary and files: {file_paths}'
