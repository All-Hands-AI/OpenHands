import os
from collections import defaultdict
from difflib import SequenceMatcher

from openhands.linter.base import BaseLinter, LinterException, LintResult
from openhands.linter.languages.python import PythonLinter
from openhands.linter.languages.treesitter import TreesitterBasicLinter


class DefaultLinter(BaseLinter):
    def __init__(self):
        self.linters: dict[str, list[BaseLinter]] = defaultdict(list)
        self.linters['.py'] = [PythonLinter()]

        # Add treesitter linter as a fallback for all linters
        self.basic_linter = TreesitterBasicLinter()
        for extension in self.basic_linter.supported_extensions:
            self.linters[extension].append(self.basic_linter)
        self._supported_extensions = list(self.linters.keys())

    @property
    def supported_extensions(self) -> list[str]:
        return self._supported_extensions

    def lint(self, file_path: str) -> list[LintResult]:
        if not os.path.isabs(file_path):
            raise LinterException(f'File path {file_path} is not an absolute path')
        file_extension = os.path.splitext(file_path)[1]

        linters: list[BaseLinter] = self.linters.get(file_extension, [])
        for linter in linters:
            res = linter.lint(file_path)
            # We always return the first linter's result (higher priority)
            if res:
                return res
        return []

    def lint_file_diff(
        self, original_file_path: str, updated_file_path: str
    ) -> list[LintResult]:
        """Only return lint errors that are introduced by the diff.

        Args:
            original_file_path: The original file path.
            updated_file_path: The updated file path.

        Returns:
            A list of lint errors that are introduced by the diff.
        """
        # 1. Lint the original and updated file
        original_lint_errors: list[LintResult] = self.lint(original_file_path)
        updated_lint_errors: list[LintResult] = self.lint(updated_file_path)

        # 2. Load the original and updated file content
        with open(original_file_path, 'r') as f:
            old_lines = f.readlines()
        with open(updated_file_path, 'r') as f:
            new_lines = f.readlines()

        # 3. Get line numbers that are changed & unchanged
        # Map the line number of the original file to the updated file
        # NOTE: this only works for lines that are not changed (i.e., equal)
        old_to_new_line_no_mapping: dict[int, int] = {}
        replace_or_inserted_lines: list[int] = []
        for (
            tag,
            old_idx_start,
            old_idx_end,
            new_idx_start,
            new_idx_end,
        ) in SequenceMatcher(
            isjunk=None,
            a=old_lines,
            b=new_lines,
        ).get_opcodes():
            if tag == 'equal':
                for idx, _ in enumerate(old_lines[old_idx_start:old_idx_end]):
                    old_to_new_line_no_mapping[old_idx_start + idx + 1] = (
                        new_idx_start + idx + 1
                    )
            elif tag == 'replace' or tag == 'insert':
                for idx, _ in enumerate(old_lines[old_idx_start:old_idx_end]):
                    replace_or_inserted_lines.append(new_idx_start + idx + 1)
            else:
                # omit the case of delete
                pass

        # 4. Get pre-existing errors in unchanged lines
        # increased error elsewhere introduced by the newlines
        # i.e., we omit errors that are already in original files and report new one
        new_line_no_to_original_errors: dict[int, list[LintResult]] = defaultdict(list)
        for error in original_lint_errors:
            if error.line in old_to_new_line_no_mapping:
                new_line_no_to_original_errors[
                    old_to_new_line_no_mapping[error.line]
                ].append(error)

        # 5. Select errors from lint results in new file to report
        selected_errors = []
        for error in updated_lint_errors:
            # 5.1. Error introduced by replace/insert
            if error.line in replace_or_inserted_lines:
                selected_errors.append(error)
            # 5.2. Error introduced by modified lines that impacted
            #      the unchanged lines that HAVE pre-existing errors
            elif error.line in new_line_no_to_original_errors:
                # skip if the error is already reported
                # or add if the error is new
                if not any(
                    original_error.message == error.message
                    and original_error.column == error.column
                    for original_error in new_line_no_to_original_errors[error.line]
                ):
                    selected_errors.append(error)
            # 5.3. Error introduced by modified lines that impacted
            #      the unchanged lines that have NO pre-existing errors
            else:
                selected_errors.append(error)

        # 6. Sort errors by line and column
        selected_errors.sort(key=lambda x: (x.line, x.column))
        return selected_errors
