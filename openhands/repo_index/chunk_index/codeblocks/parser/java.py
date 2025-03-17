from tree_sitter_languages import get_language

from .parser import CodeParser


class JavaParser(CodeParser):
    def __init__(self, **kwargs):
        language = get_language('java')
        super().__init__(language, **kwargs)
        # super().__init__(Language(java.language()), **kwargs)
        self.queries = []
        self.queries.extend(self._build_queries('java.scm'))
        self.gpt_queries = []
