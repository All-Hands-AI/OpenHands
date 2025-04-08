from dataclasses import dataclass, field
from typing import List

from openhands.core.schema import ActionType
from openhands.events.action.action import Action


@dataclass
class ContextReorganizationAction(Action):
    """This action reorganizes the context by providing a structured summary and important files.

    This is useful when:
    1. The context becomes too large
    2. The user explicitly requests it
    3. There's redundant or outdated information (like old file versions)

    Attributes:
        summary (str): A structured summary of the conversation, containing all important
            information and insights.
        files (List[dict]): A list of files from the workspace to add to the context.
            Each file is represented as a dict with 'path' and optionally 'view_range'.
        action (str): The action type, namely ActionType.CONTEXT_REORGANIZATION.
    """

    summary: str = ''
    files: List[dict] = field(default_factory=list)
    action: str = ActionType.CONTEXT_REORGANIZATION

    @property
    def message(self) -> str:
        file_paths = (
            ', '.join([f['path'] for f in self.files]) if self.files else 'no files'
        )
        return f'Reorganizing context with summary and files: {file_paths}'
