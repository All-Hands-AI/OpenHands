import os

from openhands.linter.base import BaseLinter, LinterException, LintResult
from openhands.linter.languages.python import PythonLinter

# from openhands.linter.languages.typescript import TypeScriptLinter
from openhands.linter.languages.treesitter import TreesitterBasicLinter


class Linter(BaseLinter):
    def __init__(self):
        self.linters: dict[str, list[BaseLinter]] = {
            '.py': [PythonLinter()],
            # '.ts': TypeScriptLinter(),
            # '.tsx': TypeScriptLinter(),
            # '.js': TypeScriptLinter(),
            # '.jsx': TypeScriptLinter(),
        }
        self._supported_extensions = list(self.linters.keys())

        # Add treesitter linter as a fallback for all linters
        self.basic_linter = TreesitterBasicLinter()
        for extension in self.basic_linter.supported_extensions:
            if extension in self.linters:
                self.linters[extension].append(self.basic_linter)

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
