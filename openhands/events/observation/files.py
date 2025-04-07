"""File-related observation classes for tracking file operations."""

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
        """Get a human-readable message describing the file read operation."""
        return f'I read the file {self.path}.'

    def __str__(self) -> str:
        """Get a string representation of the file read observation."""
        return f'[Read from {self.path} is successful.]\n{self.content}'


@dataclass
class FileWriteObservation(Observation):
    """This data class represents a file write operation."""

    path: str
    observation: str = ObservationType.WRITE

    @property
    def message(self) -> str:
        """Get a human-readable message describing the file write operation."""
        return f'I wrote to the file {self.path}.'

    def __str__(self) -> str:
        """Get a string representation of the file write observation."""
        return f'[Write to {self.path} is successful.]\n{self.content}'


@dataclass
class FileEditObservation(Observation):
    """This data class represents a file edit operation.

    The observation includes both the old and new content of the file, and can
    generate a diff visualization showing the changes. The diff is computed lazily
    and cached to improve performance.

    The .content property can either be:
      - Git diff in LLM-based editing mode
      - the rendered message sent to the LLM in OH_ACI mode (e.g., "The file /path/to/file.txt is created with the provided content.")
    """

    path: str = ''
    prev_exist: bool = False
    old_content: str | None = None
    new_content: str | None = None
    observation: str = ObservationType.EDIT
    impl_source: FileEditSource = FileEditSource.LLM_BASED_EDIT
    diff: str | None = (
        None  # The raw diff between old and new content, used in OH_ACI mode
    )
    _diff_cache: str | None = (
        None  # Cache for the diff visualization, used in LLM-based editing mode
    )

    @property
    def message(self) -> str:
        """Get a human-readable message describing the file edit operation."""
        return f'I edited the file {self.path}.'

    def get_edit_groups(self, n_context_lines: int = 2) -> list[dict[str, list[str]]]:
        """Get the edit groups showing changes between old and new content.

        Args:
            n_context_lines: Number of context lines to show around each change.

        Returns:
            A list of edit groups, where each group contains before/after edits.
        """
        if self.old_content is None or self.new_content is None:
            return []
        old_lines = self.old_content.split('\n')
        new_lines = self.new_content.split('\n')
        # Borrowed from difflib.unified_diff to directly parse into structured format
        edit_groups: list[dict] = []
        for group in SequenceMatcher(None, old_lines, new_lines).get_grouped_opcodes(
            n_context_lines
        ):
            # Take the max line number in the group
            _indent_pad_size = len(str(group[-1][3])) + 1  # +1 for "*" prefix
            cur_group: dict[str, list[str]] = {
                'before_edits': [],
                'after_edits': [],
            }
            for tag, i1, i2, j1, j2 in group:
                if tag == 'equal':
                    for idx, line in enumerate(old_lines[i1:i2]):
                        line_num = i1 + idx + 1
                        cur_group['before_edits'].append(
                            f'{line_num:>{_indent_pad_size}}|{line}'
                        )
                    for idx, line in enumerate(new_lines[j1:j2]):
                        line_num = j1 + idx + 1
                        cur_group['after_edits'].append(
                            f'{line_num:>{_indent_pad_size}}|{line}'
                        )
                    continue
                if tag in {'replace', 'delete'}:
                    for idx, line in enumerate(old_lines[i1:i2]):
                        line_num = i1 + idx + 1
                        cur_group['before_edits'].append(
                            f'-{line_num:>{_indent_pad_size-1}}|{line}'
                        )
                if tag in {'replace', 'insert'}:
                    for idx, line in enumerate(new_lines[j1:j2]):
                        line_num = j1 + idx + 1
                        cur_group['after_edits'].append(
                            f'+{line_num:>{_indent_pad_size-1}}|{line}'
                        )
            edit_groups.append(cur_group)
        return edit_groups

    def visualize_diff(
        self,
        n_context_lines: int = 2,
        change_applied: bool = True,
    ) -> str:
        """Visualize the diff of the file edit. Used in the LLM-based editing mode.

        Instead of showing the diff line by line, this function shows each hunk
        of changes as a separate entity.

        Args:
            n_context_lines: Number of context lines to show before/after changes.
            change_applied: Whether changes are applied. If false, shows as
                attempted edit.

        Returns:
            A string containing the formatted diff visualization.
        """
        # Use cached diff if available
        if self._diff_cache is not None:
            return self._diff_cache

        # Check if there are any changes
        if change_applied and self.old_content == self.new_content:
            msg = '(no changes detected. Please make sure your edits change '
            msg += 'the content of the existing file.)\n'
            self._diff_cache = msg
            return self._diff_cache

        edit_groups = self.get_edit_groups(n_context_lines=n_context_lines)

        if change_applied:
            header = f'[Existing file {self.path} is edited with '
            header += f'{len(edit_groups)} changes.]'
        else:
            header = f"[Changes are NOT applied to {self.path} - Here's how "
            header += 'the file looks like if changes are applied.]'
        result = [header]

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

        # Cache the result
        self._diff_cache = '\n'.join(result)
        return self._diff_cache

    def __str__(self) -> str:
        """Get a string representation of the file edit observation."""
        if self.impl_source == FileEditSource.OH_ACI:
            return self.content

        if not self.prev_exist:
            assert (
                self.old_content == ''
            ), 'old_content should be empty if the file is new (prev_exist=False).'
            return f'[New file {self.path} is created with the provided content.]\n'

        # Use cached diff if available, otherwise compute it
        return self.visualize_diff().rstrip() + '\n'
