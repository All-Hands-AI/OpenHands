import difflib
import glob
import logging
import os
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel

from .codeblocks import get_parser_by_path
from .codeblocks.codeblocks import CodeBlockTypeGroup, CodeBlockType
from .codeblocks.module import Module
from .codeblocks.parser.python import PythonParser

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
    module: Optional[Module] = None

    dirty: bool = False

    @classmethod
    def from_file(cls, repo_path: str, file_path: str):
        with open(os.path.join(repo_path, file_path), "r") as f:
            parser = get_parser_by_path(file_path)
            if parser:
                content = f.read()
                module = parser.parse(content)
            else:
                module = None
            return cls(file_path=file_path, content=content, module=module)

    @classmethod
    def from_content(cls, file_path: str, content: str):
        parser = PythonParser()
        module = parser.parse(content)
        return cls(file_path=file_path, content=content, module=module)

    @property
    def supports_codeblocks(self):
        return self.module is not None

    def update_content_by_line_numbers(
        self, start_line_index: int, end_line_index: int, replacement_content: str
    ) -> UpdateResult:
        replacement_lines = replacement_content.split("\n")

        # Strip empty lines from the start and end
        while replacement_lines and replacement_lines[0].strip() == "":
            replacement_lines.pop(0)

        while replacement_lines and replacement_lines[-1].strip() == "":
            replacement_lines.pop()

        original_lines = self.content.split("\n")

        replacement_lines = remove_duplicate_lines(
            replacement_lines, original_lines[end_line_index:]
        )

        updated_lines = (
            original_lines[:start_line_index]
            + replacement_lines
            + original_lines[end_line_index:]
        )
        updated_content = "\n".join(updated_lines)
        logger.info(
            f"Updating content for {self.file_path} from line {start_line_index} to {end_line_index} with {len(replacement_lines)} lines. The updated file has {len(updated_lines)} lines."
        )

        return self.update_content(updated_content)

    def update_content(self, updated_content: str) -> UpdateResult:
        diff = do_diff(self.file_path, self.content, updated_content)
        if diff:
            parser = get_parser_by_path(self.file_path)
            if parser:
                module = parser.parse(updated_content)
                if not module.children:
                    return UpdateResult(
                        file_path=self.file_path,
                        updated=False,
                        diff=diff,
                        error="The updated code is invalid.",
                    )

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
                    error_response = ""
                    if error_blocks:
                        for error_block in error_blocks:
                            parent_block = error_block.find_type_group_in_parents(
                                CodeBlockTypeGroup.STRUCTURE
                            )
                            if (
                                parent_block
                                and not parent_block.type == CodeBlockType.MODULE
                            ):
                                error_response += f"{parent_block.type.name} has invalid code:\n\n```{parent_block.to_string()}\n```.\n"
                            else:
                                error_response += f"This code is invalid: \n```{error_block.to_string()}\n```.\n"

                    if new_placeholders:
                        for new_placeholder in new_placeholders:
                            parent_block = new_placeholder.find_type_group_in_parents(
                                CodeBlockTypeGroup.STRUCTURE
                            )
                            if parent_block:
                                error_response += f"{parent_block.identifier} has a placeholder `{new_placeholder.content}` indicating that it's not fully implemented. Implement the full {parent_block.type.name} or reject the request.: \n\n```{parent_block.to_string()}```\n\n"
                            else:
                                error_response += f"There is a placeholder indicating out commented code : \n```{new_placeholder.to_string()}\n```. Do the full implementation or reject the request.\n"

                    for validation_error in validation_errors:
                        error_response += f"{validation_error}\n"

                    logger.warning(
                        f"Errors in updated file {self.file_path}:\n{error_response}"
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

                logger.info(
                    f"Updated content for {self.file_path} with {len(new_span_ids)} new span ids."
                )
                self.module = module
            else:
                new_span_ids = []

            self.dirty = True
            self.content = updated_content

            return UpdateResult(
                file_path=self.file_path,
                updated=True,
                diff=diff,
                new_span_ids=new_span_ids,
            )

        return UpdateResult(file_path=self.file_path, updated=False)


class FileRepository:

    def __init__(self, repo_path: str):
        self._repo_path = repo_path
        self._files: dict[str, CodeFile] = {}

    @property
    def path(self):
        return self._repo_path

    def get_file(
        self, file_path: str, refresh: bool = False, from_origin: bool = False
    ):
        """
        Get a file from the repository.

        Args:

        """
        file = self._files.get(file_path)
        if not file or refresh or from_origin:
            full_file_path = os.path.join(self._repo_path, file_path)
            if not os.path.exists(full_file_path):
                logger.warning(f"File not found: {full_file_path}")
                return None
            if not os.path.isfile(full_file_path):
                logger.warning(f"{full_file_path} is not a file")
                return None

            with open(full_file_path, "r") as f:
                parser = get_parser_by_path(file_path)
                if parser:
                    content = f.read()
                    module = parser.parse(content, file_path)
                    file = CodeFile(file_path=file_path, content=content, module=module)
                else:
                    file = CodeFile(file_path=file_path, content=f.read())

            if refresh or not from_origin:
                self._files[file_path] = file
        return file

    def save_file(self, file_path: str, updated_content: Optional[str] = None):
        file = self._files.get(file_path)
        full_file_path = os.path.join(self._repo_path, file_path)
        with open(full_file_path, "w") as f:
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

        if not matched_files and not file_pattern.startswith("*"):
            return self.matching_files(f"**/{file_pattern}")

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
    return "".join(
        difflib.unified_diff(
            original_content.strip().splitlines(True),
            updated_content.strip().splitlines(True),
            fromfile=file_path,
            tofile=file_path,
            lineterm="\n",
        )
    )
