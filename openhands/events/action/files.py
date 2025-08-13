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
    view_range: list[int] | None = None  # ONLY used in OH_ACI mode

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

    This class supports two main modes of operation:
    1. LLM-based editing (impl_source = FileEditSource.LLM_BASED_EDIT)
    2. ACI-based editing (impl_source = FileEditSource.OH_ACI)

    Attributes:
        path (str): The path to the file being edited. Works for both LLM-based and OH_ACI editing.
        OH_ACI only arguments:
            command (str): The editing command to be performed (view, create, str_replace, insert, undo_edit, write).
            file_text (str): The content of the file to be created (used with 'create' command in OH_ACI mode).
            old_str (str): The string to be replaced (used with 'str_replace' command in OH_ACI mode).
            new_str (str): The string to replace old_str (used with 'str_replace' and 'insert' commands in OH_ACI mode).
            insert_line (int): The line number after which to insert new_str (used with 'insert' command in OH_ACI mode).
        LLM-based editing arguments:
            content (str): The content to be written or edited in the file (used in LLM-based editing and 'write' command).
            start (int): The starting line for editing (1-indexed, inclusive). Default is 1.
            end (int): The ending line for editing (1-indexed, inclusive). Default is -1 (end of file).
            thought (str): The reasoning behind the edit action.
            action (str): The type of action being performed (always ActionType.EDIT).
        runnable (bool): Indicates if the action can be executed (always True).
        security_risk (ActionSecurityRisk | None): Indicates any security risks associated with the action.
        impl_source (FileEditSource): The source of the implementation (LLM_BASED_EDIT or OH_ACI).

    Usage:
        - For LLM-based editing: Use path, content, start, and end attributes.
        - For ACI-based editing: Use path, command, and the appropriate attributes for the specific command.

    Note:
        - If start is set to -1 in LLM-based editing, the content will be appended to the file.
        - The 'write' command behaves similarly to LLM-based editing, using content, start, and end attributes.
    """

    path: str

    # OH_ACI arguments
    command: str = ''
    file_text: str | None = None
    old_str: str | None = None
    new_str: str | None = None
    insert_line: int | None = None

    # LLM-based editing arguments
    content: str = ''
    start: int = 1
    end: int = -1

    # Shared arguments
    thought: str = ''
    action: str = ActionType.EDIT
    runnable: ClassVar[bool] = True
    security_risk: ActionSecurityRisk | None = None
    impl_source: FileEditSource = FileEditSource.OH_ACI

    def __repr__(self) -> str:
        ret = '**FileEditAction**\n'
        ret += f'Path: [{self.path}]\n'
        ret += f'Thought: {self.thought}\n'

        if self.impl_source == FileEditSource.LLM_BASED_EDIT:
            ret += f'Range: [L{self.start}:L{self.end}]\n'
            ret += f'Content:\n```\n{self.content}\n```\n'
        else:  # OH_ACI mode
            ret += f'Command: {self.command}\n'
            if self.command == 'create':
                ret += f'Created File with Text:\n```\n{self.file_text}\n```\n'
            elif self.command == 'str_replace':
                ret += f'Old String: ```\n{self.old_str}\n```\n'
                ret += f'New String: ```\n{self.new_str}\n```\n'
            elif self.command == 'insert':
                ret += f'Insert Line: {self.insert_line}\n'
                ret += f'New String: ```\n{self.new_str}\n```\n'
            elif self.command == 'undo_edit':
                ret += 'Undo Edit\n'
            # We ignore "view" command because it will be mapped to a FileReadAction
        return ret
