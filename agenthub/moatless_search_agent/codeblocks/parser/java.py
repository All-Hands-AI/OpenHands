import tree_sitter_java as java
from tree_sitter import Language

from ...codeblocks.parser.parser import CodeParser


class JavaParser(CodeParser):
    def __init__(self, **kwargs):
        super().__init__(Language(java.language()), **kwargs)
        self.queries = []
        self.queries.extend(self._build_queries('java.scm'))
        self.gpt_queries = []
