from dataclasses import dataclass
from difflib import SequenceMatcher

from openhands.core.schema import ObservationType
from openhands.events.event import FileEditSource, FileReadSource
from openhands.events.observation.observation import Observation


@dataclass
class FileReadObservation(Observation):
    """This data class represents the content of a file."""

    path: str
    observation: str = ObservationType.READ
    impl_source: FileReadSource = FileReadSource.DEFAULT

    @property
    def message(self) -> str:
        return f'I read the file {self.path}.'


@dataclass
class FileWriteObservation(Observation):
    """This data class represents a file write operation"""

    path: str
    observation: str = ObservationType.WRITE

    @property
    def message(self) -> str:
        return f'I wrote to the file {self.path}.'


@dataclass
class FileEditObservation(Observation):
    """This data class represents a file edit operation"""

    # content: str will be a unified diff patch string include NO context lines
    path: str
    prev_exist: bool
    old_content: str
    new_content: str
    observation: str = ObservationType.EDIT
    impl_source: FileEditSource = FileEditSource.LLM_BASED_EDIT
    formatted_output_and_error: str = ''

    @property
    def message(self) -> str:
        return f'I edited the file {self.path}.'

    def get_edit_groups(self, n_context_lines: int = 2) -> list[dict[str, list[str]]]:
        """Get the edit groups of the file edit."""
        old_lines = self.old_content.split('\n')
        new_lines = self.new_content.split('\n')
        # Borrowed from difflib.unified_diff to directly parse into structured format.
        edit_groups: list[dict] = []
        for group in SequenceMatcher(None, old_lines, new_lines).get_grouped_opcodes(
            n_context_lines
        ):
            # take the max line number in the group
            _indent_pad_size = len(str(group[-1][3])) + 1  # +1 for the "*" prefix
            cur_group: dict[str, list[str]] = {
                'before_edits': [],
                'after_edits': [],
            }
            for tag, i1, i2, j1, j2 in group:
                if tag == 'equal':
                    for idx, line in enumerate(old_lines[i1:i2]):
                        cur_group['before_edits'].append(
                            f'{i1+idx+1:>{_indent_pad_size}}|{line}'
                        )
                    for idx, line in enumerate(new_lines[j1:j2]):
                        cur_group['after_edits'].append(
                            f'{j1+idx+1:>{_indent_pad_size}}|{line}'
                        )
                    continue
                if tag in {'replace', 'delete'}:
                    for idx, line in enumerate(old_lines[i1:i2]):
                        cur_group['before_edits'].append(
                            f'-{i1+idx+1:>{_indent_pad_size-1}}|{line}'
                        )
                if tag in {'replace', 'insert'}:
                    for idx, line in enumerate(new_lines[j1:j2]):
                        cur_group['after_edits'].append(
                            f'+{j1+idx+1:>{_indent_pad_size-1}}|{line}'
                        )
            edit_groups.append(cur_group)
        return edit_groups

    def visualize_diff(
        self,
        n_context_lines: int = 2,
        change_applied: bool = True,
    ) -> str:
        """Visualize the diff of the file edit.

        Instead of showing the diff line by line, this function
        shows each hunk of changes as a separate entity.

        Args:
            n_context_lines: The number of lines of context to show before and after the changes.
            change_applied: Whether the changes are applied to the file. If true, the file have been modified. If not, the file is not modified (due to linting errors).
        """
        if change_applied and self.content.strip() == '':
            # diff patch is empty
            return '(no changes detected. Please make sure your edits changes the content of the existing file.)\n'

        edit_groups = self.get_edit_groups(n_context_lines=n_context_lines)

        result = [
            f'[Existing file {self.path} is edited with {len(edit_groups)} changes.]'
            if change_applied
            else f"[Changes are NOT applied to {self.path} - Here's how the file looks like if changes are applied.]"
        ]

        op_type = 'edit' if change_applied else 'ATTEMPTED edit'
        for i, cur_edit_group in enumerate(edit_groups):
            if i != 0:
                result.append('-------------------------')
            result.append(f'[begin of {op_type} {i+1} / {len(edit_groups)}]')
            result.append(f'(content before {op_type})')
            result.extend(cur_edit_group['before_edits'])
            result.append(f'(content after {op_type})')
            result.extend(cur_edit_group['after_edits'])
            result.append(f'[end of {op_type} {i+1} / {len(edit_groups)}]')
        return '\n'.join(result)

    def __str__(self) -> str:
        if self.impl_source == FileEditSource.OH_ACI:
            return self.formatted_output_and_error

        ret = ''
        if not self.prev_exist:
            assert (
                self.old_content == ''
            ), 'old_content should be empty if the file is new (prev_exist=False).'
            ret += f'[New file {self.path} is created with the provided content.]\n'
            return ret.rstrip() + '\n'
        ret += self.visualize_diff()
        return ret.rstrip() + '\n'
