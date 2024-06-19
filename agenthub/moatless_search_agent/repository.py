import difflib
import glob
import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

from pydantic import BaseModel

from .codeblocks.codeblocks import CodeBlockType, CodeBlockTypeGroup
from .codeblocks.module import Module
from .codeblocks.parser.python import PythonParser
from .settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class UpdateResult:
    file_path: str
    updated: bool
    diff: Optional[str] = None
    error: Optional[str] = None
    new_span_ids: Optional[set[str]] = None


class CodeFile(BaseModel):
    file_path: str
    content: str
    module: Module

    dirty: bool = False

    @classmethod
    def from_file(cls, repo_path: str, file_path: str):
        with open(os.path.join(repo_path, file_path), 'r') as f:
            content = f.read()
            parser = PythonParser()
            module = parser.parse(content)
            return cls(file_path=file_path, content=content, module=module)

    @classmethod
    def from_content(cls, file_path: str, content: str):
        parser = PythonParser()
        module = parser.parse(content)
        return cls(file_path=file_path, content=content, module=module)

    def update_content_by_line_numbers(
        self, start_line_index: int, end_line_index: int, replacement_content: str
    ) -> UpdateResult:
        replacement_lines = replacement_content.split('\n')

        # Strip empty lines from the start and end
        while replacement_lines and replacement_lines[0].strip() == '':
            replacement_lines.pop(0)

        while replacement_lines and replacement_lines[-1].strip() == '':
            replacement_lines.pop()

        original_lines = self.content.split('\n')

        replacement_lines = remove_duplicate_lines(
            replacement_lines, original_lines[end_line_index:]
        )

        updated_lines = (
            original_lines[:start_line_index]
            + replacement_lines
            + original_lines[end_line_index:]
        )
        updated_content = '\n'.join(updated_lines)

        return self.update_content(updated_content)

    def update_content(self, updated_content: str) -> UpdateResult:
        diff = do_diff(self.file_path, self.content, updated_content)

        if diff:
            parser = PythonParser()
            module = parser.parse(updated_content)

            # TODO: Move the prompt instructions to the loop
            error_blocks = module.find_errors()
            validation_errors = module.find_validation_errors()
            existing_placeholders = self.module.find_blocks_with_type(
                CodeBlockType.COMMENTED_OUT_CODE
            )
            new_placeholders = (
                module.find_blocks_with_type(CodeBlockType.COMMENTED_OUT_CODE)
                if not existing_placeholders
                else []
            )
            if error_blocks or validation_errors or new_placeholders:
                error_response = ''
                if error_blocks:
                    for error_block in error_blocks:
                        parent_block = error_block.find_type_group_in_parents(
                            CodeBlockTypeGroup.STRUCTURE
                        )
                        if (
                            parent_block
                            and not parent_block.type == CodeBlockType.MODULE
                        ):
                            error_response += f'{parent_block.type.name} has invalid code:\n\n```{parent_block.to_string()}\n```.\n'
                        else:
                            error_response += f'This code is invalid: \n```{error_block.to_string()}\n```.\n'

                if new_placeholders:
                    for new_placeholder in new_placeholders:
                        parent_block = new_placeholder.find_type_group_in_parents(
                            CodeBlockTypeGroup.STRUCTURE
                        )
                        if parent_block:
                            error_response += f"{parent_block.identifier} has a placeholder `{new_placeholder.content}` indicating that it's not fully implemented. Implement the full {parent_block.type.name} or reject the request.: \n\n```{parent_block.to_string()}```\n\n"
                        else:
                            error_response += f'There is a placeholder indicating out commented code : \n```{new_placeholder.to_string()}\n```. Do the full implementation or reject the request.\n'

                for validation_error in validation_errors:
                    error_response += f'{validation_error}\n'

                logger.warning(
                    f'Errors in updated file {self.file_path}:\n{error_response}'
                )

                return UpdateResult(
                    file_path=self.file_path,
                    updated=False,
                    diff=diff,
                    error=error_response,
                )

            new_span_ids = module.get_all_span_ids() - set(
                self.module.get_all_span_ids()
            )
            self.dirty = True
            self.content = updated_content
            self.module = module

            return UpdateResult(
                file_path=self.file_path,
                updated=True,
                diff=diff,
                new_span_ids=new_span_ids,
            )

        return UpdateResult(file_path=self.file_path, updated=False)

    def get_line_span(
        self,
        start_line: int,
        end_line: Optional[int] = None,
        max_tokens=Settings.coder.max_tokens_in_edit_prompt,
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Find the span that covers the lines from start_line to end_line
        """

        logger.info(
            f'Get span to change in {self.file_path} from {start_line} to {end_line}'
        )

        start_block = self.module.find_first_by_start_line(start_line)
        if not start_block:
            logger.warning(
                f'No block found in {self.file_path} that starts at line {start_line}'
            )
            return None, None

        if start_block.type.group == CodeBlockTypeGroup.STRUCTURE and (
            not end_line or start_block.end_line > end_line
        ):
            struture_block = start_block
        else:
            res = start_block.find_type_group_in_parents(CodeBlockTypeGroup.STRUCTURE)

            if not res:
                logger.warning(
                    f'No parent structure found for block {start_block.path_string()}'
                )
                return None, None

            struture_block = res

        if struture_block.sum_tokens() < max_tokens:
            logger.info(
                f'Return block [{struture_block.path_string()}] ({struture_block.start_line} - {struture_block.end_line}) with {struture_block.sum_tokens()} tokens that covers the provided line span ({start_line} - {end_line})'
            )
            return struture_block.start_line, struture_block.end_line

        if not end_line:
            end_line = start_line

        original_lines = self.content.split('\n')
        if struture_block.end_line - end_line < 5:
            logger.info(
                f"Set parent block [{struture_block.path_string()}] end line {struture_block.end_line} as it's {struture_block.end_line - end_line} lines from the end of the file"
            )
            end_line = struture_block.end_line
        else:
            end_line = _get_post_end_line_index(
                end_line, struture_block.end_line, original_lines
            )
            logger.info(f'Set end line to {end_line} from the end of the parent block')

        if start_line - struture_block.start_line < 5:
            logger.info(
                f"Set parent block [{struture_block.path_string()}] start line {struture_block.start_line} as it's {start_line - struture_block.start_line} lines from the start of the file"
            )
            start_line = struture_block.start_line
        else:
            start_line = _get_pre_start_line(
                start_line, struture_block.start_line, original_lines
            )
            logger.info(
                f'Set start line to {start_line} from the start of the parent block'
            )

        return start_line, end_line


_parser = PythonParser()


class FileRepository:
    def __init__(self, repo_path: str):
        self._repo_path = repo_path
        self._files: dict[str, CodeFile] = {}

    @property
    def path(self):
        return self._repo_path

    def get_file(self, file_path: str, refresh: bool = False):
        file = self._files.get(file_path)
        if not file or refresh:
            full_file_path = os.path.join(self._repo_path, file_path)
            if not os.path.exists(full_file_path):
                logger.warning(f'File not found: {full_file_path}')
                return None
            if not os.path.isfile(full_file_path):
                logger.warning(f'{full_file_path} is not a file')
                return None

            with open(full_file_path, 'r') as f:
                content = f.read()
                module = _parser.parse(content)
                file = CodeFile(file_path=file_path, content=content, module=module)
                self._files[file_path] = file

        return file

    def save_file(self, file_path: str, updated_content: Optional[str] = None):
        file = self._files.get(file_path)
        if not file:
            logger.warning(f'File {file_path} not found in repository')
            return

        full_file_path = os.path.join(self._repo_path, file.file_path)
        logger.debug(f'Writing updated content to {full_file_path}')

        with open(full_file_path, 'w') as f:
            updated_content = updated_content or file.module.to_string()
            f.write(updated_content)

        file.dirty = False

    def save(self):
        for file in self._files.values():
            if file.dirty:
                self.save_file(file.file_path, file.content)

    def matching_files(self, file_pattern: str):
        matched_files = []
        for matched_file in glob.iglob(
            file_pattern, root_dir=self._repo_path, recursive=True
        ):
            matched_files.append(matched_file)

        if not matched_files and not file_pattern.startswith('*'):
            return self.matching_files(f'**/{file_pattern}')

        return matched_files

    def find_files(self, file_patterns: list[str]) -> set[str]:
        found_files = set()
        for file_pattern in file_patterns:
            matched_files = self.matching_files(file_pattern)
            found_files.update(matched_files)

        return found_files

    def has_matching_files(self, file_pattern: str):
        for matched_file in glob.iglob(
            file_pattern, root_dir=self._repo_path, recursive=True
        ):
            return True
        return False

    def file_match(self, file_pattern: str, file_path: str):
        match = False
        for matched_file in glob.iglob(
            file_pattern, root_dir=self._repo_path, recursive=True
        ):
            if matched_file == file_path:
                match = True
                break
        return match


def remove_duplicate_lines(replacement_lines, original_lines):
    """
    Removes overlapping lines at the end of replacement_lines that match the beginning of original_lines.
    """
    if not replacement_lines or not original_lines:
        return replacement_lines

    max_overlap = min(len(replacement_lines), len(original_lines))

    for overlap in range(max_overlap, 0, -1):
        if replacement_lines[-overlap:] == original_lines[:overlap]:
            return replacement_lines[:-overlap]

    return replacement_lines


def do_diff(
    file_path: str, original_content: str, updated_content: str
) -> Optional[str]:
    return ''.join(
        difflib.unified_diff(
            original_content.strip().splitlines(True),
            updated_content.strip().splitlines(True),
            fromfile=file_path,
            tofile=file_path,
            lineterm='\n',
        )
    )


def _get_pre_start_line(
    start_line: int, min_start_line: int, content_lines: List[str], max_lines: int = 4
) -> int:
    if start_line > len(content_lines):
        raise ValueError(
            f'start_line {start_line} is out of range ({len(content_lines)}).'
        )

    if start_line - min_start_line < max_lines:
        return min_start_line

    start_line_index = start_line - 1
    start_search_index = max(0, start_line_index - 1)
    end_search_index = max(min_start_line, start_line_index - max_lines)

    non_empty_indices = []

    for idx in range(start_search_index, end_search_index - 1, -1):
        if content_lines[idx].strip() != '':
            non_empty_indices.append(idx)

    # Check if any non-empty line was found within the search range
    if non_empty_indices:
        return non_empty_indices[-1] + 1

    # If no non-empty lines were found, check the start_line itself
    if content_lines[start_line_index].strip() != '':
        return start_line_index + 1

    # If the start_line is also empty, raise an exception
    raise ValueError('No non-empty line found within 3 lines above the start_line.')


def _get_post_end_line_index(
    end_line: int, max_end_line: int, content_lines: List[str], max_lines: int = 4
) -> int:
    if end_line < 1 or end_line > len(content_lines):
        raise IndexError('end_line is out of range.')

    if max_end_line - end_line < max_lines:
        return max_end_line

    end_line_index = end_line - 1
    start_search_index = min(len(content_lines) - 1, end_line_index + 1)
    end_search_index = min(max_end_line - 1, end_line_index + max_lines)

    non_empty_indices = []

    for idx in range(start_search_index, end_search_index + 1):
        if content_lines[idx].strip() != '':
            non_empty_indices.append(idx)

    # Check if any non-empty line was found within the search range
    if non_empty_indices:
        return non_empty_indices[-1] + 1

    # If no non-empty lines were found, check the end_line itself
    if content_lines[end_line_index].strip() != '':
        return end_line_index + 1

    # If the end_line is also empty, raise an exception
    raise ValueError('No non-empty line found within 3 lines after the end_line.')
