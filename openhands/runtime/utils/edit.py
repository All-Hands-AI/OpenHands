import difflib
import os
import re
import tempfile
from abc import ABC, abstractmethod
from typing import Any

from openhands_aci.utils.diff import get_diff

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    FileEditAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
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

    # ==========================================================================
    # Fenced Diff / LLM Diff Edit Logic (Adapted from Aider principles)
    # ==========================================================================

    def _exact_replace(
        self, original_lines: list[str], search_lines: list[str], replace_lines: list[str]
    ) -> list[str] | None:
        """Attempts an exact character-for-character replacement."""
        search_tuple = tuple(search_lines)
        search_len = len(search_lines)
        if search_len == 0:
            return None # Cannot replace empty search block exactly

        for i in range(len(original_lines) - search_len + 1):
            original_tuple = tuple(original_lines[i : i + search_len])
            if search_tuple == original_tuple:
                return original_lines[:i] + replace_lines + original_lines[i + search_len :]
        return None

    def _whitespace_flexible_replace(
        self, original_lines: list[str], search_lines: list[str], replace_lines: list[str]
    ) -> list[str] | None:
        """Attempts replacement ignoring consistent leading whitespace differences."""
        search_len = len(search_lines)
        if search_len == 0:
            return None

        # Calculate min leading whitespace in search block (ignoring blank lines)
        search_leading_spaces = [len(s) - len(s.lstrip(' ')) for s in search_lines if s.strip()]
        min_search_leading = min(search_leading_spaces) if search_leading_spaces else 0
        stripped_search_lines = [s[min_search_leading:] if s.strip() else s for s in search_lines]
        stripped_search_tuple = tuple(stripped_search_lines)

        for i in range(len(original_lines) - search_len + 1):
            original_chunk = original_lines[i : i + search_len]

            # Calculate min leading whitespace in original chunk
            original_leading_spaces = [len(s) - len(s.lstrip(' ')) for s in original_chunk if s.strip()]
            min_original_leading = min(original_leading_spaces) if original_leading_spaces else 0
            leading_whitespace_prefix = ' ' * min_original_leading

            # Strip original chunk consistently
            stripped_original_lines = [s[min_original_leading:] if s.strip() else s for s in original_chunk]
            stripped_original_tuple = tuple(stripped_original_lines)

            if stripped_search_tuple == stripped_original_tuple:
                # Match found! Apply original leading whitespace to replace_lines
                adjusted_replace_lines = [
                    leading_whitespace_prefix + rline[min_search_leading:] if rline.strip() else rline
                    for rline in replace_lines
                ]
                return original_lines[:i] + adjusted_replace_lines + original_lines[i + search_len :]
        return None

    def _find_most_similar_block(
        self, original_lines: list[str], search_lines: list[str], context_lines: int = 5
    ) -> tuple[str | None, float]:
        """Finds the block in original_lines most similar to search_lines."""
        if not search_lines or not original_lines:
            return None, 0.0

        search_len = len(search_lines)
        best_ratio = 0.0
        best_match_start_idx = -1

        matcher = difflib.SequenceMatcher(isjunk=None, a=search_lines)
        for i in range(len(original_lines) - search_len + 1):
            chunk = original_lines[i : i + search_len]
            matcher.set_seq2(chunk)
            ratio = matcher.ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match_start_idx = i

        if best_match_start_idx != -1:
            start = max(0, best_match_start_idx - context_lines)
            end = min(len(original_lines), best_match_start_idx + search_len + context_lines)
            context_chunk = original_lines[start:end]

            # Add markers to indicate the likely match within the context
            marked_chunk = []
            for idx, line in enumerate(context_chunk):
                current_original_line_idx = start + idx
                if best_match_start_idx <= current_original_line_idx < best_match_start_idx + search_len:
                     marked_chunk.append(f'> {line}') # Mark lines within the best match range
                else:
                     marked_chunk.append(f'  {line}')

            return '\n'.join(marked_chunk), best_ratio
        else:
            return None, 0.0

    def _apply_llm_diff_edit(self, action: FileEditAction, original_content: str) -> tuple[str | None, Observation | None]:
        """Helper to apply a single LLM_DIFF edit block."""
        # Use standard splitlines (no keepends)
        original_lines = original_content.splitlines()
        # Use getattr to safely access search/replace, defaulting to empty string if not present
        search_content = getattr(action, 'search', '')
        replace_content = getattr(action, 'replace', '')
        search_lines = search_content.splitlines()
        replace_lines = replace_content.splitlines()

        # Handle empty search block (create file / append)
        if not search_content.strip():
            # Append if file exists, otherwise content is replace_content
            # Ensure single newline separation if original content exists and doesn't end with newline
            separator = '\n' if original_content and not original_content.endswith('\n') else ''
            updated_content = original_content + separator + replace_content
            # Preserve original trailing newline status
            if original_content.endswith('\n') and not updated_content.endswith('\n'):
                 updated_content += '\n'
            elif not original_content.endswith('\n') and updated_content.endswith('\n'):
                 # This case is less likely, but if replace_content added a newline, remove it if original didn't have one
                 updated_content = updated_content.rstrip('\n')
            return updated_content, None

        # Attempt exact match
        updated_lines = self._exact_replace(original_lines, search_lines, replace_lines)

        # Attempt whitespace flexible match if exact failed
        if updated_lines is None:
            updated_lines = self._whitespace_flexible_replace(original_lines, search_lines, replace_lines)

        # Handle match failure
        if updated_lines is None:
            logger.warning(f'Failed to apply diff to {action.path}')
            similar_block, ratio = self._find_most_similar_block(original_lines, search_lines)
            error_msg = (
                f'Failed to apply edit to {action.path}.\n'
                'The SEARCH block did not match the file content exactly or with flexible whitespace.\n\n'
                '--- FAILED SEARCH BLOCK ---\n'
                f'{search_content}\n'
                '--- END FAILED SEARCH BLOCK ---\n'
            )
            if similar_block and ratio > 0.6: # Threshold from Aider
                 error_msg += (
                    f'\n--- MOST SIMILAR BLOCK FOUND (similarity: {ratio:.2f}) ---\n'
                    f'{similar_block}\n'
                    '--- END MOST SIMILAR BLOCK ---\n\n'
                    'Please check the SEARCH block and the file content and try again.'
                 )
            else:
                 error_msg += '\nNo similar block found.'

            return None, ErrorObservation(error_msg)

        # Match successful - join with newline
        final_content = '\n'.join(updated_lines)
        
        return final_content, None


    def llm_diff_edit(self, action: FileEditAction) -> Observation:
        """Applies a fenced diff edit parsed directly from LLM output."""
        if action.impl_source != 'llm_diff':
             # Should not happen if dispatch is correct, but safety check
             raise ValueError(f"llm_diff_edit called with incorrect action source: {action.impl_source}")

        # Read original file or handle creation
        read_obs = self.read(FileReadAction(path=action.path))
        original_content = ""
        prev_exist = True

        if isinstance(read_obs, ErrorObservation) and 'File not found'.lower() in read_obs.content.lower():
            logger.info(f'File {action.path} not found. Attempting to create based on edit.')
            prev_exist = False
            # Check if it's a valid creation (empty search block)
            search_content = getattr(action, 'search', '')
            if search_content.strip():
                return ErrorObservation(f"File {action.path} not found and SEARCH block is not empty. Cannot apply edit.")
            # Content will be handled by _apply_llm_diff_edit
        elif isinstance(read_obs, ErrorObservation):
            # Other read error
            return read_obs
        elif isinstance(read_obs, FileReadObservation):
            original_content = read_obs.content
        else:
             return ErrorObservation(f"Unexpected observation type received when reading {action.path}: {type(read_obs)}")

        # Apply the edit logic
        updated_content, error_obs = self._apply_llm_diff_edit(action, original_content)

        if error_obs:
            return error_obs
        if updated_content is None:
             # Should have been caught by error_obs, but safety check
             return ErrorObservation(f"Edit application failed for {action.path}. Be more careful! You can try smaller or larger edit blocks.")


        # Lint the updated content (optional)
        diff = get_diff(original_content, updated_content, action.path)
        if self.config.sandbox.enable_auto_lint:
            suffix = os.path.splitext(action.path)[1]
            lint_error_obs = self._get_lint_error(
                suffix, original_content, updated_content, action.path, diff
            )
            if lint_error_obs is not None:
                # Attach original diff to lint error message for context
                lint_error_obs.content += (
                    '\n\n--- ORIGINAL DIFF ATTEMPTED ---\n'
                    f'{diff}\n'
                    '--- END ORIGINAL DIFF ATTEMPTED ---'
                )
                return lint_error_obs

        # Write the final content
        write_obs = self.write(FileWriteAction(path=action.path, content=updated_content))
        if isinstance(write_obs, ErrorObservation):
            return write_obs # Return write error if it occurs

        # Return success observation
        return FileEditObservation(
            content=diff, # Return the calculated diff
            path=action.path,
            prev_exist=prev_exist,
            old_content=original_content,
            new_content=updated_content,
            impl_source=action.impl_source, # Pass source along
        )
