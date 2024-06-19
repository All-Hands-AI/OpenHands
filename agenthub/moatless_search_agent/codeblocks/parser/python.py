import logging
from typing import Any

import tree_sitter_python as tspython
from tree_sitter import Language

from ...codeblocks.codeblocks import (
    CodeBlock,
    CodeBlockType,
    ReferenceScope,
    RelationshipType,
    ValidationError,
)
from ...codeblocks.parser.parser import (
    CodeParser,
    NodeMatch,
    commented_out_keywords,
)

child_block_types = ['ERROR', 'block']

block_delimiters = [':']

logger = logging.getLogger(__name__)


class PythonParser(CodeParser):
    def __init__(self, **kwargs):
        language = Language(tspython.language())

        super().__init__(language, **kwargs)

        self.queries = []
        self.queries.extend(self._build_queries('python.scm'))

        if self.apply_gpt_tweaks:
            self.gpt_queries.extend(self._build_queries('python_gpt.scm'))

    @property
    def language(self):
        return 'python'

    def pre_process(self, codeblock: CodeBlock, node_match: NodeMatch):
        if (
            codeblock.type == CodeBlockType.FUNCTION
            and codeblock.identifier == '__init__'
        ):
            codeblock.type = CodeBlockType.CONSTRUCTOR

        # Handle line breaks after assignment without \
        if (
            codeblock.type == CodeBlockType.ASSIGNMENT
            and codeblock.content_lines[0].strip().endswith('=')
            and node_match.check_child
            and node_match.first_child
            and node_match.check_child.start_point[0]
            < node_match.first_child.start_point[0]
        ):
            logger.warning(
                f'Parsed block with type ASSIGNMENT with line break but no ending \\: {codeblock.content_lines[0]}'
            )
            codeblock.content_lines[0] = codeblock.content_lines[0] + ' \\'

    def post_process(self, codeblock: CodeBlock):
        if codeblock.type == CodeBlockType.COMMENT and self.is_outcommented_code(
            codeblock.content
        ):
            codeblock.type = CodeBlockType.COMMENTED_OUT_CODE

        if codeblock.type == CodeBlockType.ASSIGNMENT:
            for reference in codeblock.relationships:
                reference.type = RelationshipType.TYPE

        new_references: Any = []
        for reference in codeblock.relationships:
            # Set parent class path as reference path on self
            if reference.path and reference.path[0] == 'self':
                class_block = codeblock.find_type_in_parents(CodeBlockType.CLASS)
                if class_block:
                    reference.scope = ReferenceScope.CLASS
                    if len(reference.path) > 1:
                        reference.path = class_block.full_path() + reference.path[1:2]
                        reference.identifier = codeblock.identifier

            # Set parent classes super class path as reference path on super()
            # TODO: make a solution where this can be derived even further (by checking import)
            if reference.path and reference.path[0] == 'super()':
                class_block = codeblock.find_type_in_parents(CodeBlockType.CLASS)
                if class_block:
                    is_a_rel = [
                        rel
                        for rel in class_block.relationships
                        if rel.type == RelationshipType.IS_A
                    ]
                    if is_a_rel:
                        super_class = codeblock.root().find_by_path(is_a_rel[0].path)

                        if super_class:
                            reference.path = (
                                super_class.full_path() + reference.path[1:2]
                            )
                            reference.identifier = super_class.identifier

        codeblock.relationships.extend(new_references)

        if (
            codeblock.type in [CodeBlockType.CLASS, CodeBlockType.FUNCTION]
            and len(codeblock.children) == 1
            and codeblock.children[0].type == CodeBlockType.COMMENTED_OUT_CODE
        ):
            codeblock.type = CodeBlockType.COMMENTED_OUT_CODE

        function_names = set()
        class_names = set()
        for child in codeblock.children:
            if child.type == CodeBlockType.FUNCTION:
                if child.identifier in function_names:
                    child.validation_errors.append(
                        ValidationError(
                            error=f'Duplicate function name: {child.identifier}'
                        )
                    )
                function_names.add(child.identifier)
            if child.type == CodeBlockType.CLASS:
                if child.identifier in class_names:
                    child.validation_errors.append(
                        ValidationError(
                            error=f'Duplicate class name: {child.identifier}'
                        )
                    )
                class_names.add(child.identifier)

    def is_outcommented_code(self, comment):
        return comment.startswith('# ...') or any(
            keyword in comment.lower() for keyword in commented_out_keywords
        )
