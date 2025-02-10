from dataclasses import dataclass
from typing import ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import Action, ActionSecurityRisk
from openhands.events.event import FileEditSource, FileReadSource


@dataclass
class FileReadAction(Action):
    """Reads a file from a given path.
    Can be set to read specific lines using start and end
    Default lines 0:-1 (whole file)
    """

    path: str
    start: int = 0
    end: int = -1
    thought: str = ''
    action: str = ActionType.READ
    runnable: ClassVar[bool] = True
    security_risk: ActionSecurityRisk | None = None
    impl_source: FileReadSource = FileReadSource.DEFAULT
    translated_ipython_code: str = ''  # translated openhands-aci IPython code

    @property
    def message(self) -> str:
        return f'Reading file: {self.path}'


@dataclass
class FileWriteAction(Action):
    """Writes a file to a given path.
    Can be set to write specific lines using start and end
    Default lines 0:-1 (whole file)
    """

    path: str
    content: str
    start: int = 0
    end: int = -1
    thought: str = ''
    action: str = ActionType.WRITE
    runnable: ClassVar[bool] = True
    security_risk: ActionSecurityRisk | None = None

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'

    def __repr__(self) -> str:
        return (
            f'**FileWriteAction**\n'
            f'Path: {self.path}\n'
            f'Range: [L{self.start}:L{self.end}]\n'
            f'Thought: {self.thought}\n'
            f'Content:\n```\n{self.content}\n```\n'
        )


@dataclass
class FileEditAction(Action):
    """Edits a file using various commands including view, create, str_replace, insert, and undo_edit.

    Can be set to edit specific lines using start and end (1-index, inclusive) if the file is too long.
    Default lines 1:-1 (whole file).

    If start is set to -1, the FileEditAction will simply append the content to the file.
    """

    path: str
    command: str
    content: str = ''
    start: int = 1
    end: int = -1
    thought: str = ''
    action: str = ActionType.EDIT
    runnable: ClassVar[bool] = True
    security_risk: ActionSecurityRisk | None = None
    impl_source: FileEditSource = FileEditSource.LLM_BASED_EDIT
    translated_ipython_code: str = ''
    file_text: str = ''
    old_str: str = ''
    new_str: str = ''
    insert_line: int = None
    view_range: list[int] = None

    def __repr__(self) -> str:
        ret = '**FileEditAction**\n'
        ret += f'Command: {self.command}\n'
        ret += f'Thought: {self.thought}\n'
        ret += f'Path: [{self.path}]\n'
        if self.command in ['view', 'create', 'str_replace', 'insert']:
            if self.command == 'view' and self.view_range:
                ret += f'View Range: {self.view_range}\n'
            elif self.command == 'create':
                ret += f'File Text:\n```\n{self.file_text}\n```\n'
            elif self.command == 'str_replace':
                ret += f'Old String: {self.old_str}\n'
                ret += f'New String: {self.new_str}\n'
            elif self.command == 'insert':
                ret += f'Insert Line: {self.insert_line}\n'
                ret += f'New String: {self.new_str}\n'
        else:
            ret += f'Range: [L{self.start}:L{self.end}]\n'
            ret += f'Content:\n```\n{self.content}\n```\n'
        return ret
