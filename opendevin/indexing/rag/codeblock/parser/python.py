import tree_sitter_python as tspython
from tree_sitter import Language

from .parser import CodeParser


class PythonParser(CodeParser):
    def __init__(self, **kwargs) -> None:
        language = Language(tspython.language())

        super().__init__(language, **kwargs)

        self.queries = []
        self.queries.extend(self._build_queries('python.scm'))
