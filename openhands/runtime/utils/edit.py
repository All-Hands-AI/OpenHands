import difflib
import os
import re
import tempfile
from abc import ABC, abstractmethod

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    FileEditAction,
    FileReadAction,
    FileWriteAction,
)
from openhands.events.observation import (
    ErrorObservation,
    FileEditObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from openhands.llm.llm import LLM
from openhands.runtime.plugins.agent_skills.file_ops.file_ops import _lint_file

SYS_MSG = """Your job is to produce a new version of the file based on the old version and the
provided draft of the new version. The provided draft may be incomplete (it may skip lines) and/or incorrectly indented. You should try to apply the changes present in the draft to the old version, and output a new version of the file.
NOTE:
- The output file should be COMPLETE and CORRECTLY INDENTED. Do not omit any lines, and do not change any lines that are not part of the changes.
- You should output the new version of the file by wrapping the new version of the file content in a ``` block.
- If there's no explicit comment to remove the existing code, we should keep them and append the new code to the end of the file.
"""

USER_MSG = """
HERE IS THE OLD VERSION OF THE FILE:
```
{old_contents}
```

HERE IS THE DRAFT OF THE NEW VERSION OF THE FILE:
```
{draft_changes}
```

GIVE ME THE NEW VERSION OF THE FILE.
""".strip()


def _extract_code(string):
    pattern = r'```(?:\w*\n)?(.*?)```'
    matches = re.findall(pattern, string, re.DOTALL)
    if not matches:
        return None
    return matches[0]


def get_new_file_contents(
    llm: LLM, old_contents: str, draft_changes: str, num_retries: int = 3
) -> str | None:
    while num_retries > 0:
        messages = [
            {'role': 'system', 'content': SYS_MSG},
            {
                'role': 'user',
                'content': USER_MSG.format(
                    old_contents=old_contents, draft_changes=draft_changes
                ),
            },
        ]
        resp = llm.completion(messages=messages)
        new_contents = _extract_code(resp['choices'][0]['message']['content'])
        if new_contents is not None:
            return new_contents
        num_retries -= 1
    return None


def get_diff(old_contents: str, new_contents: str, filepath: str) -> str:
    diff = list(
        difflib.unified_diff(
            old_contents.strip().split('\n'),
            new_contents.strip().split('\n'),
            fromfile=filepath,
            tofile=filepath,
        )
    )
    return '\n'.join(map(lambda x: x.rstrip(), diff))


class FileEditRuntimeInterface(ABC):
    config: AppConfig

    @abstractmethod
    def read(self, action: FileReadAction) -> Observation:
        pass

    @abstractmethod
    def write(self, action: FileWriteAction) -> Observation:
        pass


class FileEditRuntimeMixin(FileEditRuntimeInterface):
    # Most LLMs have output token limit of 4k tokens.
    # This restricts the number of lines we can edit to avoid exceeding the token limit.
    MAX_LINES_TO_EDIT = 300

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        llm_config = self.config.get_llm_config()

        if llm_config.draft_editor is None:
            raise RuntimeError(
                'ERROR: Draft editor LLM is not set. Please set a draft editor LLM in the config.'
            )

        self.draft_editor_llm = LLM(llm_config.draft_editor)
        logger.info(
            f'[Draft edit functionality] enabled with LLM: {self.draft_editor_llm}'
        )

    def _validate_range(
        self, start: int, end: int, total_lines: int
    ) -> Observation | None:
        # start and end are 1-indexed and inclusive
        if (
            (start < 1 and start != -1)
            or start > total_lines
            or (start > end and end != -1 and start != -1)
        ):
            return ErrorObservation(
                f'Invalid range for editing: start={start}, end={end}, total lines={total_lines}. start must be >= 1 and <={total_lines} (total lines of the edited file), start <= end, or start == -1 (append to the end of the file).'
            )
        if (
            (end < 1 and end != -1)
            or end > total_lines
            or (end < start and start != -1 and end != -1)
        ):
            return ErrorObservation(
                f'Invalid range for editing: start={start}, end={end}, total lines={total_lines}. end must be >= 1 and <= {total_lines} (total lines of the edited file), end >= start, or end == -1 (to edit till the end of the file).'
            )
        return None

    def edit(self, action: FileEditAction) -> Observation:
        obs = self.read(FileReadAction(path=action.path))
        if (
            isinstance(obs, ErrorObservation)
            and 'File not found'.lower() in obs.content.lower()
        ):
            # directly write the new content
            obs = self.write(
                FileWriteAction(path=action.path, content=action.content.strip())
            )
            if isinstance(obs, ErrorObservation):
                return obs
            assert isinstance(obs, FileWriteObservation)
            return FileEditObservation(
                content=get_diff('', action.content, action.path),
                path=action.path,
                prev_exist=False,
            )
        assert isinstance(
            obs, FileReadObservation
        ), f'Expected FileReadObservation, got {type(obs)}'

        original_file_content = obs.content
        old_file_lines = original_file_content.split('\n')
        # NOTE: start and end are 1-indexed
        start = action.start
        end = action.end
        # validate the range
        error = self._validate_range(start, end, len(old_file_lines))
        if error is not None:
            return error

        # append to the end of the file
        if start == -1:
            updated_content = '\n'.join(old_file_lines + action.content.split('\n'))
            diff = get_diff(original_file_content, updated_content, action.path)
            # Lint the updated content
            if self.config.sandbox.enable_auto_lint:
                suffix = os.path.splitext(action.path)[1]
                with tempfile.NamedTemporaryFile(
                    suffix=suffix, mode='w+', encoding='utf-8'
                ) as temp_file:
                    temp_file.write(updated_content)
                    temp_file.flush()
                    lint_error, _ = _lint_file(temp_file.name)
                    if lint_error:
                        error_message = f'\n=== Linting failed for edited file [{action.path}] ===\n{lint_error}\n===\nChanges tried:\n{diff}\n==='
                        return ErrorObservation(error_message)
            obs = self.write(FileWriteAction(path=action.path, content=updated_content))
            return FileEditObservation(content=diff, path=action.path, prev_exist=True)

        # Get the 0-indexed start and end
        start_idx = start - 1
        if end != -1:
            # remove 1 to make it 0-indexed
            # then add 1 since the `end` is inclusive
            end_idx = end - 1 + 1
        else:
            # end == -1 means the user wants to edit till the end of the file
            end_idx = len(old_file_lines)

        length_of_range = end_idx - start_idx
        if length_of_range > self.MAX_LINES_TO_EDIT:
            return ErrorObservation(
                f'The range of lines to edit is too long. The maximum number of lines allowed to edit at once is {self.MAX_LINES_TO_EDIT}.'
            )

        content_to_edit = '\n'.join(old_file_lines[start_idx:end_idx])
        _edited_content = get_new_file_contents(
            self.draft_editor_llm, content_to_edit, action.content
        )
        if _edited_content is None:
            return ErrorObservation(
                'Failed to get new file contents. '
                'Please try to reduce the number of edits and try again.'
            )

        # piece the updated content with the unchanged content
        updated_lines = (
            old_file_lines[:start_idx]
            + _edited_content.split('\n')
            + old_file_lines[end_idx:]
        )
        updated_content = '\n'.join(updated_lines)
        diff = get_diff(original_file_content, updated_content, action.path)

        # Lint the updated content
        if self.config.sandbox.enable_auto_lint:
            suffix = os.path.splitext(action.path)[1]
            with tempfile.NamedTemporaryFile(
                suffix=suffix, mode='w+', encoding='utf-8'
            ) as temp_file:
                temp_file.write(updated_content)
                temp_file.flush()
                lint_error, _ = _lint_file(temp_file.name)
                if lint_error:
                    error_message = f'\n=== Linting failed for edited file [{action.path}] ===\n{lint_error}\n===\nChanges tried:\n{diff}\n==='
                    return ErrorObservation(error_message)

        obs = self.write(FileWriteAction(path=action.path, content=updated_content))
        return FileEditObservation(content=diff, path=action.path, prev_exist=True)
