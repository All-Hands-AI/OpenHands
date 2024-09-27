import os
from collections import defaultdict

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
