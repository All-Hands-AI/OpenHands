import os
import re
import tempfile
from abc import ABC, abstractmethod
from typing import Any

from openhands_aci.utils.diff import get_diff  # type: ignore

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    FileEditAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from openhands.events.event import FileEditSource
from openhands.events.observation import (
    ErrorObservation,
    FileEditObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from openhands.linter import DefaultLinter
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics
from openhands.utils.chunk_localizer import Chunk, get_top_k_chunk_matches

SYS_MSG = """Your job is to produce a new version of the file based on the old version and the
provided draft of the new version. The provided draft may be incomplete (it may skip lines) and/or incorrectly indented. You should try to apply the changes present in the draft to the old version, and output a new version of the file.
NOTE:
- The output file should be COMPLETE and CORRECTLY INDENTED. Do not omit any lines, and do not change any lines that are not part of the changes.
- You should output the new version of the file by wrapping the new version of the file content in a ``` block.
- If there's no explicit comment to remove the existing code, we should keep them and append the new code to the end of the file.
- If there's placeholder comments like `# no changes before` or `# no changes here`, we should replace these comments with the original code near the placeholder comments.
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
IMPORTANT:
- There should be NO placeholder comments like `# no changes before` or `# no changes here`. They should be replaced with the original code near the placeholder comments.
- The output file should be COMPLETE and CORRECTLY INDENTED. Do not omit any lines, and do not change any lines that are not part of the changes.
""".strip()


def _extract_code(string: str) -> str | None:
    pattern = r'```(?:\w*\n)?(.*?)```'
    matches = re.findall(pattern, string, re.DOTALL)
    if not matches:
        return None
    return str(matches[0])


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


class FileEditRuntimeInterface(ABC):
    config: AppConfig

    @abstractmethod
    def read(self, action: FileReadAction) -> Observation:
        pass

    @abstractmethod
    def write(self, action: FileWriteAction) -> Observation:
        pass

    @abstractmethod
    def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        pass


class FileEditRuntimeMixin(FileEditRuntimeInterface):
    # Most LLMs have output token limit of 4k tokens.
    # This restricts the number of lines we can edit to avoid exceeding the token limit.
    MAX_LINES_TO_EDIT = 300

    def __init__(self, enable_llm_editor: bool, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.enable_llm_editor = enable_llm_editor

        if not self.enable_llm_editor:
            return

        draft_editor_config = self.config.get_llm_config('draft_editor')

        # manually set the model name for the draft editor LLM to distinguish token costs
        llm_metrics = Metrics(model_name='draft_editor:' + draft_editor_config.model)
        if draft_editor_config.caching_prompt:
            logger.debug(
                'It is not recommended to cache draft editor LLM prompts as it may incur high costs for the same prompt. '
                'Automatically setting caching_prompt=false.'
            )
            draft_editor_config.caching_prompt = False

        self.draft_editor_llm = LLM(draft_editor_config, metrics=llm_metrics)
        logger.debug(
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

    def _get_lint_error(
        self,
        suffix: str,
        old_content: str,
        new_content: str,
        filepath: str,
        diff: str,
    ) -> ErrorObservation | None:
        linter = DefaultLinter()
        # Copy the original file to a temporary file (with the same ext) and lint it
        with (
            tempfile.NamedTemporaryFile(
                suffix=suffix, mode='w+', encoding='utf-8'
            ) as original_file_copy,
            tempfile.NamedTemporaryFile(
                suffix=suffix, mode='w+', encoding='utf-8'
            ) as updated_file_copy,
        ):
            # Lint the original file
            original_file_copy.write(old_content)
            original_file_copy.flush()

            # Lint the updated file
            updated_file_copy.write(new_content)
            updated_file_copy.flush()

            updated_lint_error = linter.lint_file_diff(
                original_file_copy.name, updated_file_copy.name
            )

            if len(updated_lint_error) > 0:
                _obs = FileEditObservation(
                    content=diff,
                    path=filepath,
                    prev_exist=True,
                    old_content=old_content,
                    new_content=new_content,
                )
                error_message = (
                    (
                        f'\n[Linting failed for edited file {filepath}. {len(updated_lint_error)} lint errors found.]\n'
                        '[begin attempted changes]\n'
                        f'{_obs.visualize_diff(change_applied=False)}\n'
                        '[end attempted changes]\n'
                    )
                    + '-' * 40
                    + '\n'
                )
                error_message += '-' * 20 + 'First 5 lint errors' + '-' * 20 + '\n'
                for i, lint_error in enumerate(updated_lint_error[:5]):
                    error_message += f'[begin lint error {i}]\n'
                    error_message += lint_error.visualize().strip() + '\n'
                    error_message += f'[end lint error {i}]\n'
                    error_message += '-' * 40 + '\n'
                return ErrorObservation(error_message)
        return None

    def llm_based_edit(self, action: FileEditAction) -> Observation:
        obs = self.read(FileReadAction(path=action.path))
        if (
            isinstance(obs, ErrorObservation)
            and 'File not found'.lower() in obs.content.lower()
        ):
            logger.debug(
                f'Agent attempted to edit a file that does not exist. Creating the file. Error msg: {obs.content}'
            )
            # directly write the new content
            obs = self.write(
                FileWriteAction(path=action.path, content=action.content.strip())
            )
            if isinstance(obs, ErrorObservation):
                return obs
            if not isinstance(obs, FileWriteObservation):
                raise ValueError(
                    f'Expected FileWriteObservation, got {type(obs)}: {str(obs)}'
                )
            return FileEditObservation(
                content=get_diff('', action.content, action.path),
                path=action.path,
                prev_exist=False,
                old_content='',
                new_content=action.content,
            )
        if not isinstance(obs, FileReadObservation):
            raise ValueError(
                f'Expected FileReadObservation, got {type(obs)}: {str(obs)}'
            )

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

                error_obs = self._get_lint_error(
                    suffix,
                    original_file_content,
                    updated_content,
                    action.path,
                    diff,
                )
                if error_obs is not None:
                    return error_obs

            obs = self.write(FileWriteAction(path=action.path, content=updated_content))
            return FileEditObservation(
                content=diff,
                path=action.path,
                prev_exist=True,
                old_content=original_file_content,
                new_content=updated_content,
            )

        # Get the 0-indexed start and end
        start_idx = start - 1
        if end != -1:
            # remove 1 to make it 0-indexed
            # then add 1 since the `end` is inclusive
            end_idx = end - 1 + 1
        else:
            # end == -1 means the user wants to edit till the end of the file
            end_idx = len(old_file_lines)

        # Get the range of lines to edit - reject if too long
        length_of_range = end_idx - start_idx
        if length_of_range > self.MAX_LINES_TO_EDIT + 1:
            error_msg = (
                f'[Edit error: The range of lines to edit is too long.]\n'
                f'[The maximum number of lines allowed to edit at once is {self.MAX_LINES_TO_EDIT}. '
                f'Got (L{start_idx + 1}-L{end_idx}) {length_of_range} lines.]\n'  # [start_idx, end_idx), so no need to + 1
            )
            # search for relevant ranges to hint the agent
            topk_chunks: list[Chunk] = get_top_k_chunk_matches(
                text=original_file_content,
                query=action.content,  # edit draft as query
                k=3,
                max_chunk_size=20,  # lines
            )
            error_msg += (
                'Here are some snippets that maybe relevant to the provided edit.\n'
            )
            for i, chunk in enumerate(topk_chunks):
                error_msg += f'[begin relevant snippet {i + 1}. Line range: L{chunk.line_range[0]}-L{chunk.line_range[1]}. Similarity: {chunk.normalized_lcs}]\n'
                error_msg += f'[Browse around it via `open_file("{action.path}", {(chunk.line_range[0] + chunk.line_range[1]) // 2})`]\n'
                error_msg += chunk.visualize() + '\n'
                error_msg += f'[end relevant snippet {i + 1}]\n'
                error_msg += '-' * 40 + '\n'

            error_msg += 'Consider using `open_file` to explore around the relevant snippets if needed.\n'
            error_msg += f'**IMPORTANT**: Please REDUCE the range of edits to less than {self.MAX_LINES_TO_EDIT} lines by setting `start` and `end` in the edit action (e.g. `<file_edit path="{action.path}" start=[PUT LINE NUMBER HERE] end=[PUT LINE NUMBER HERE] />`). '

            return ErrorObservation(error_msg)

        content_to_edit = '\n'.join(old_file_lines[start_idx:end_idx])
        self.draft_editor_llm.reset()
        _edited_content = get_new_file_contents(
            self.draft_editor_llm, content_to_edit, action.content
        )
        if _edited_content is None:
            ret_err = ErrorObservation(
                'Failed to get new file contents. '
                'Please try to reduce the number of edits and try again.'
            )
            ret_err.llm_metrics = self.draft_editor_llm.metrics
            return ret_err

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
            error_obs = self._get_lint_error(
                suffix, original_file_content, updated_content, action.path, diff
            )
            if error_obs is not None:
                error_obs.llm_metrics = self.draft_editor_llm.metrics
                return error_obs

        obs = self.write(FileWriteAction(path=action.path, content=updated_content))
        ret_obs = FileEditObservation(
            content=diff,
            path=action.path,
            prev_exist=True,
            old_content=original_file_content,
            new_content=updated_content,
        )
        ret_obs.llm_metrics = self.draft_editor_llm.metrics
        return ret_obs

    def _exact_replace(
        self, whole_lines: list[str], part_lines: list[str], replace_lines: list[str]
    ) -> str | None:
        """Attempts to find an exact match of part_lines within whole_lines and replace it.
        Adapted from Aider's perfect_replace logic."""
        part_tup = tuple(part_lines)
        part_len = len(part_lines)

        if not part_len:  # Cannot search for an empty block
            return None

        for i in range(len(whole_lines) - part_len + 1):
            whole_tup = tuple(whole_lines[i : i + part_len])
            if part_tup == whole_tup:
                res_lines = (
                    whole_lines[:i] + replace_lines + whole_lines[i + part_len :]
                )
                # Ensure the result ends with a newline if the original or replacement did
                # or if the original file ended with one.
                res = ''.join(res_lines)
                if (
                    (part_lines and part_lines[-1].endswith('\n'))
                    or (replace_lines and replace_lines[-1].endswith('\n'))
                    or (whole_lines and whole_lines[-1].endswith('\n'))
                ):
                    if not res.endswith('\n'):
                        res += '\n'
                return res
        return None

    # Fenced diff is adapted from the logic in Aider
    # Copyright Paul Gauthier
    # Licensed under Apache 2.0: http://www.apache.org/licenses/LICENSE-2.0
    def fenced_diff_edit(self, action: FileEditAction) -> Observation:
        """Handles FileEditAction with FENCED_DIFF source using SEARCH/REPLACE blocks."""
        logger.info(f'Executing fenced diff edit for: {action.path}')
        assert (
            action.search_block is not None
        ), 'search_block cannot be None for FENCED_DIFF'
        assert (
            action.replace_block is not None
        ), 'replace_block cannot be None for FENCED_DIFF'

        # 1. Read file content using the interface method
        read_obs = self.read(FileReadAction(path=action.path))

        original_content: str
        prev_exist: bool = True
        if (
            isinstance(read_obs, ErrorObservation)
            and 'File not found'.lower() in read_obs.content.lower()
        ):
            logger.info(
                f'File not found for fenced diff: {action.path}. Will attempt to create if search_block is empty.'
            )
            original_content = ''
            prev_exist = False
        elif isinstance(read_obs, ErrorObservation):
            return read_obs  # Propagate other read errors
        elif isinstance(read_obs, FileReadObservation):
            original_content = read_obs.content
        else:
            return ErrorObservation(
                f'Unexpected observation type {type(read_obs)} received during read for fenced diff.'
            )

        # 2. Handle Empty Search Block (Append/Create)
        if not action.search_block.strip():
            if not prev_exist:
                logger.info(f'Creating new file {action.path} with content.')
                new_content = action.replace_block
            else:
                logger.info(f'Appending content to {action.path}.')
                if original_content and not original_content.endswith('\n'):
                    original_content += '\n'
                new_content = original_content + action.replace_block

            # Write the new content using the interface method
            write_obs = self.write(
                FileWriteAction(path=action.path, content=new_content)
            )
            if isinstance(write_obs, ErrorObservation):
                return write_obs

            diff = get_diff(original_content, new_content, action.path)
            return FileEditObservation(
                content=f'Appended content to {action.path}'
                if prev_exist
                else f'Created file {action.path}',
                path=action.path,
                old_content=original_content,
                new_content=new_content,
                impl_source=FileEditSource.FENCED_DIFF,
                diff=diff,
                prev_exist=prev_exist,
            )

        # 3. Implement Exact Search/Replace Logic
        original_lines = original_content.splitlines(keepends=True)
        search_lines = action.search_block.splitlines(keepends=True)
        replace_lines = action.replace_block.splitlines(keepends=True)

        # Ensure search/replace blocks are not empty lists if input was just whitespace
        if action.search_block and not search_lines:
            search_lines = ['\n'] * action.search_block.count('\n') + (
                [''] if not action.search_block.endswith('\n') else []
            )
        if action.replace_block and not replace_lines:
            replace_lines = ['\n'] * action.replace_block.count('\n') + (
                [''] if not action.replace_block.endswith('\n') else []
            )
        if not action.replace_block:
            replace_lines = []

        new_content_str = self._exact_replace(
            original_lines, search_lines, replace_lines
        )

        # 4. Handle errors (search_block not found)
        if new_content_str is None:
            # TODO: Optionally implement more flexible matching here (e.g., whitespace)
            logger.warning(f'Exact search_block not found in {action.path}')
            error_message = f'Failed to apply fenced diff edit: The specified search_block was not found exactly in {action.path}.\n'
            error_message += 'SEARCH BLOCK:\n```\n' + action.search_block + '\n```'
            return ErrorObservation(error_message)

        # 5. Write modified content back using the interface method
        write_obs = self.write(
            FileWriteAction(path=action.path, content=new_content_str)
        )
        if isinstance(write_obs, ErrorObservation):
            return write_obs

        # 6. Return FileEditObservation
        diff = get_diff(original_content, new_content_str, action.path)
        return FileEditObservation(
            content=f'Applied fenced diff edit to {action.path}',
            path=action.path,
            old_content=original_content,
            new_content=new_content_str,
            impl_source=FileEditSource.FENCED_DIFF,
            diff=diff,
            prev_exist=prev_exist,
        )
