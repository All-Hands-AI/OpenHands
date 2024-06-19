import logging
import re
from dataclasses import dataclass, field
from importlib import resources
from typing import Any, Callable, List, Optional, Tuple

import networkx as nx
from llama_index.core import get_tokenizer
from tree_sitter import Language, Node, Parser

from ...codeblocks.codeblocks import (
    BlockSpan,
    CodeBlock,
    CodeBlockType,
    CodeBlockTypeGroup,
    Parameter,
    ReferenceScope,
    Relationship,
    RelationshipType,
    SpanType,
)
from ...codeblocks.module import Module
from ...codeblocks.parser.comment import get_comment_symbol

commented_out_keywords = ['rest of the code', 'existing code', 'other code']
child_block_types = ['ERROR', 'block']
module_types = ['program', 'module']

logger = logging.getLogger(__name__)


@dataclass
class NodeMatch:
    block_type: Optional[CodeBlockType] = None
    identifier_node: Optional[Node] = None
    first_child: Optional[Node] = None
    last_child: Optional[Node] = None
    check_child: Optional[Node] = None
    parameters: List[Tuple[Node, Optional[Node]]] = field(default_factory=list)
    relationships: List[Tuple[Node, str]] = field(default_factory=list)
    query: Optional[str] = None


def _find_type(node: Node, type: str):
    for i, child in enumerate(node.children):
        if child.type == type:
            return i, child
    return None, None


def find_type(node: Node, types: List[str]):
    for child in node.children:
        if child.type in types:
            return child
    return None


def find_nested_type(node: Node, type: str, levels: int = -1):
    if levels == 0:
        return None
    if node.type == type:
        return node
    for child in node.children:
        found_node = find_nested_type(child, type, levels - 1)
        if found_node:
            return found_node
    return None


class CodeParser:
    def __init__(
        self,
        language: Language,
        encoding: str = 'utf8',
        max_tokens_in_span: int = 500,
        min_tokens_for_docs_span: int = 100,
        index_callback: Optional[Callable[[CodeBlock], None]] = None,
        tokenizer: Optional[Callable[[str], List]] = None,
        apply_gpt_tweaks: bool = False,
        debug: bool = False,
    ):
        try:
            self.tree_parser = Parser()
            self.tree_parser.set_language(language)
            self.tree_language = language
        except Exception as e:
            logger.warning(f'Could not get parser for language {language}.')
            raise e
        self.apply_gpt_tweaks = apply_gpt_tweaks
        self.index_callback = index_callback
        self.debug = debug
        self.encoding = encoding
        self.gpt_queries: Any = []
        self.queries: Any = []

        # TODO: How to handle these in a thread safe way?
        self.spans_by_id: Any = {}
        self.comments_with_no_span: Any = []
        self._span_counter: Any = {}
        self._previous_block: Any = None

        # TODO: Move this to CodeGraph
        self._graph: Optional[nx.DiGraph] = None

        self.tokenizer = tokenizer or get_tokenizer()
        self._max_tokens_in_span = max_tokens_in_span
        self._min_tokens_for_docs_span = min_tokens_for_docs_span

    @property
    def language(self):
        pass

    def _extract_node_type(self, query: str):
        pattern = r'\(\s*(\w+)'
        match = re.search(pattern, query)
        if match:
            return match.group(1)
        else:
            return None

    def _build_queries(self, query_file: str):
        with resources.open_text(
            'agenthub.moatless_search_agent.codeblocks.parser.queries', query_file
        ) as file:
            query_list = file.read().strip().split('\n\n')
            parsed_queries = []
            for i, query in enumerate(query_list):
                try:
                    node_type = self._extract_node_type(query)
                    parsed_queries.append(
                        (
                            f'{query_file}:{i+1}',
                            node_type,
                            self.tree_language.query(query),
                        )
                    )
                except Exception as e:
                    logging.error(f'Could not parse query {query}:{i+1}')
                    raise e
            return parsed_queries

    def parse_code(
        self,
        content_bytes: bytes,
        node: Node,
        start_byte: int = 0,
        level: int = 0,
        file_path: Optional[str] = None,
        parent_block: Optional[CodeBlock] = None,
        current_span: Optional[BlockSpan] = None,
    ) -> Tuple[CodeBlock, Node, BlockSpan]:
        node_match: Optional[NodeMatch] = None
        if node.type == 'ERROR' or any(
            child.type == 'ERROR' for child in node.children
        ):
            node_match = NodeMatch(block_type=CodeBlockType.ERROR)
            self.debug_log(f'Found error node {node.type}')
        else:
            node_match = self.find_in_tree(node)
        assert node_match is not None, f'node_match is None for node {node}'

        pre_code = content_bytes[start_byte : node.start_byte].decode(self.encoding)
        end_line = node.end_point[0]

        if node_match.first_child:
            end_byte = self.get_previous(node_match.first_child, node)
        else:
            end_byte = node.end_byte

        code = content_bytes[node.start_byte : end_byte].decode(self.encoding)

        if node_match.identifier_node:
            identifier = content_bytes[
                node_match.identifier_node.start_byte : node_match.identifier_node.end_byte
            ].decode(self.encoding)
        else:
            identifier = None

        relationships = self.create_references(
            code, content_bytes, identifier, node_match
        )
        parameters = self.create_parameters(content_bytes, node_match, relationships)

        if parent_block:
            code_block = CodeBlock(
                type=node_match.block_type,
                identifier=identifier,
                parent=parent_block,
                previous=self._previous_block,
                parameters=parameters,
                relationships=relationships,
                span_ids=set(),
                start_line=node.start_point[0] + 1,
                end_line=end_line + 1,
                pre_code=pre_code,
                content=code,
                language=self.language,
                tokens=self._count_tokens(code),
                children=[],
                properties={
                    'query': node_match.query,
                    'tree_sitter_type': node.type,
                },
            )

            self._previous_block.next = code_block
            self._previous_block = code_block

            self.pre_process(code_block, node_match)

            if code_block.identifier:
                identifier = code_block.identifier
            else:
                if code_block.content:
                    identifier = code_block.content.split('\n')[0].strip()[0:25]
                    identifier = re.sub(r'\W+', '_', identifier)
                else:
                    identifier = code_block.type.value.lower()  # type: ignore

            # Set a unique identifier on each code block
            # TODO: Just count occurrences of the identifier
            existing_identifiers = [
                b.identifier for b in parent_block.children if b.type == code_block.type
            ]
            if identifier in existing_identifiers:
                code_block.identifier = (
                    f'{code_block.identifier}_{len(existing_identifiers)}'
                )
            else:
                code_block.identifier = identifier

            if (
                code_block.type == CodeBlockType.COMMENT
                and current_span
                and current_span.span_type != SpanType.DOCUMENTATION
                and len(current_span.block_paths) > 1
            ):
                # TODO: Find a more robust way to connect comments to the right span
                self.comments_with_no_span.append(code_block)
            else:
                new_span = self._create_new_span(
                    current_span=current_span, block=code_block
                )
                if new_span:
                    current_span = new_span
                    self.spans_by_id[current_span.span_id] = current_span
                    code_block.span_ids.add(current_span.span_id)
                else:
                    assert current_span is not None, 'current_span is None'
                    current_span.end_line = code_block.end_line

                for comment_block in self.comments_with_no_span:
                    comment_block.belongs_to_span = current_span
                    current_span.block_paths.append(comment_block.full_path())
                    current_span.tokens += comment_block.tokens

                current_span.block_paths.append(code_block.full_path())
                current_span.tokens += code_block.tokens

                code_block.belongs_to_span = current_span
                code_block.span_ids.add(current_span.span_id)

                self.comments_with_no_span = []

            if self._graph:
                self._graph.add_node(code_block.path_string(), block=code_block)

            for relationship in relationships:
                self._graph.add_edge(
                    code_block.path_string(), '.'.join(relationship.path)
                )

        else:
            current_span = None
            code_block = Module(
                type=CodeBlockType.MODULE,
                identifier=None,
                file_path=file_path,
                content='',
                spans_by_id={},
                start_line=node.start_point[0] + 1,
                end_line=end_line + 1,
                language=self.language,
                children=[],
                properties={
                    'query': node_match.query,
                    'tree_sitter_type': node.type,
                },
            )
            self._previous_block = code_block

        next_node = node_match.first_child

        self.debug_log(
            f"""Created code block
    content: {code_block.content[:50]}
    block_type: {code_block.type}
    node_type: {node.type}
    next_node: {next_node.type if next_node else "none"}
    first_child: {node_match.first_child}
    last_child: {node_match.last_child}
    start_byte: {start_byte}
    node.start_byte: {node.start_byte}
    node.end_byte: {node.end_byte}"""
        )

        index = 0

        while next_node:
            if (
                next_node.children and next_node.type == 'block'
            ):  # TODO: This should be handled in get_block_definition
                next_node = next_node.children[0]

            self.debug_log(
                f'next  [{level}]: -> {next_node.type} - {next_node.start_byte}'
            )

            child_block, child_last_node, child_span = self.parse_code(
                content_bytes,
                next_node,
                start_byte=end_byte,
                level=level + 1,
                parent_block=code_block,
                current_span=current_span,
            )

            if not current_span or child_span.span_id != current_span.span_id:
                current_span = child_span

            code_block.append_child(child_block)

            index += 1

            if child_last_node:
                self.debug_log(f'next  [{level}]: child_last_node -> {child_last_node}')
                next_node = child_last_node

            end_byte = next_node.end_byte

            self.debug_log(
                f"""next  [{level}]
    last_child -> {node_match.last_child}
    next_node -> {next_node}
    next_node.next_sibling -> {next_node.next_sibling}
    end_byte -> {end_byte}
"""
            )
            if next_node == node_match.last_child:
                break
            elif next_node.next_sibling:
                next_node = next_node.next_sibling
            else:
                next_parent_node = self.get_parent_next(
                    next_node, node_match.check_child or node
                )
                if next_parent_node == next_node:
                    next_node = None
                else:
                    next_node = next_parent_node

        self.debug_log(f'end   [{level}]: {code_block.content}')

        for comment_block in self.comments_with_no_span:
            comment_block.belongs_to_span = current_span
            if current_span:
                comment_block.span_ids.add(current_span.span_id)
                current_span.block_paths.append(comment_block.full_path())
                current_span.tokens += comment_block.tokens

        self.comments_with_no_span = []

        self.post_process(code_block)

        self.add_to_index(code_block)

        # TODO: Find a way to remove the Space end block
        if level == 0 and not node.parent and node.end_byte > end_byte:
            space_block = CodeBlock(
                type=CodeBlockType.SPACE,
                identifier=None,
                pre_code=content_bytes[end_byte : node.end_byte].decode(self.encoding),
                parent=code_block,
                start_line=end_line + 1,
                end_line=node.end_point[0] + 1,
                content='',
            )
            code_block.append_child(space_block)

        return code_block, next_node, current_span or BlockSpan()

    def is_commented_out_code(self, node: Node):
        comment = node.text.decode('utf8').strip()
        return comment.startswith(f'{get_comment_symbol(self.language)} ...') or any(
            keyword in comment.lower() for keyword in commented_out_keywords
        )

    def find_in_tree(self, node: Node) -> Optional[NodeMatch]:
        if self.apply_gpt_tweaks:
            match = self.find_match_with_gpt_tweaks(node)
            if match:
                self.debug_log(
                    f'find_in_tree() GPT match: {match.block_type} on {node}'
                )
                return match

        match = self.find_match(node)
        if match:
            self.debug_log(
                f'find_in_tree() Found match on node type {node.type} with block type {match.block_type}'
            )
            return match
        else:
            self.debug_log(
                f'find_in_tree() Found no match on node type {node.type} set block type {CodeBlockType.CODE}'
            )
            return NodeMatch(block_type=CodeBlockType.CODE)

    def find_match_with_gpt_tweaks(self, node: Node) -> Optional[NodeMatch]:
        for label, node_type, query in self.gpt_queries:
            if node_type and node.type != node_type and node_type != '_':
                continue
            match = self._find_match(node, query, label, capture_from_parent=True)
            if match:
                self.debug_log(
                    f'find_match_with_gpt_tweaks() Found match on node {node.type} with query {label}'
                )
                if not match.query:
                    match.query = label
                return match

        return None

    def find_match(self, node: Node) -> Optional[NodeMatch]:
        self.debug_log(f'find_match() node type {node.type}')
        for label, node_type, query in self.queries:
            if node_type and node.type != node_type and node_type != '_':
                continue
            match = self._find_match(node, query, label)
            if match:
                self.debug_log(
                    f'find_match() Found match on node {node.type} with query {label}'
                )
                if not match.query:
                    match.query = label
                return match

        return None

    def _find_match(
        self, node: Node, query, label: str, capture_from_parent: bool = False
    ) -> Optional[NodeMatch]:
        if capture_from_parent:
            captures = query.captures(node.parent)
        else:
            captures = query.captures(node)

        node_match = NodeMatch()

        if not captures:
            return None

        root_node = None

        for found_node, tag in captures:
            self.debug_log(f'[{label}] Found tag {tag} on node {found_node}')

            if tag == 'root' and not root_node and node == found_node:
                self.debug_log(f'[{label}] Root node {found_node}')
                root_node = found_node

            if not root_node:
                continue

            if tag == 'no_children' and found_node.children:
                return None

            if tag == 'check_child':
                self.debug_log(f'[{label}] Check child {found_node}')
                node_match_res = self.find_match(found_node)
                if node_match_res:
                    node_match_res.check_child = found_node
                return node_match_res

            if tag == 'parse_child':
                self.debug_log(f'[{label}] Parse child {found_node}')

                child_match = self.find_match(found_node)
                if child_match:
                    if child_match.relationships:
                        self.debug_log(
                            f'[{label}] Found {len(child_match.relationships)} references on child {found_node}'
                        )
                        node_match.relationships = child_match.relationships
                    if child_match.parameters:
                        self.debug_log(
                            f'[{label}] Found {len(child_match.parameters)} parameters on child {found_node}'
                        )
                        node_match.parameters.extend(child_match.parameters)
                    if child_match.first_child:
                        node_match.first_child = child_match.first_child

            if tag == 'identifier' and not node_match.identifier_node:
                node_match.identifier_node = found_node

            if tag == 'child.first' and not node_match.first_child:
                node_match.first_child = found_node

            if tag == 'child.last' and not node_match.last_child:
                node_match.last_child = found_node

            if tag == 'parameter.identifier':
                node_match.parameters.append((found_node, None))

            if tag == 'parameter.type' and node_match.parameters:
                node_match.parameters[-1] = (node_match.parameters[-1][0], found_node)

            if root_node and tag.startswith('reference'):
                node_match.relationships.append((found_node, tag))

            if not node_match.block_type:
                node_match.block_type = CodeBlockType.from_string(tag)

        if node_match.block_type:
            self.debug_log(
                f'[{label}] Return match with type {node_match.block_type} for node {node}'
            )
            return node_match

        return None

    def create_references(self, code, content_bytes, identifier, node_match):
        references = []
        if node_match.block_type == CodeBlockType.IMPORT and node_match.relationships:
            module_nodes = [
                ref for ref in node_match.relationships if ref[1] == 'reference.module'
            ]
            if module_nodes:
                module_reference_id = self.get_content(
                    module_nodes[0][0], content_bytes
                )
                if len(node_match.relationships) > 1:
                    for ref_node in node_match.relationships:
                        if ref_node == module_nodes[0]:
                            continue
                        elif ref_node[1] == 'reference.alias':
                            reference_id = self.get_content(ref_node[0], content_bytes)
                            references.append(
                                Relationship(
                                    scope=ReferenceScope.EXTERNAL,
                                    type=RelationshipType.IMPORTS,
                                    identifier=reference_id,
                                    path=[],
                                    external_path=[module_reference_id],
                                )
                            )
                        else:
                            reference_id = self.get_content(ref_node[0], content_bytes)
                            references.append(
                                Relationship(
                                    scope=ReferenceScope.EXTERNAL,
                                    type=RelationshipType.IMPORTS,
                                    identifier=reference_id,
                                    path=[reference_id],
                                    external_path=[module_reference_id],
                                )
                            )
                else:
                    references.append(
                        Relationship(
                            scope=ReferenceScope.EXTERNAL,
                            type=RelationshipType.IMPORTS,
                            identifier=module_reference_id,
                            external_path=[module_reference_id],
                        )
                    )
        else:
            for reference in node_match.relationships:
                reference_id = self.get_content(reference[0], content_bytes)

                reference_id_path = reference_id.split('.')

                if not reference_id_path:
                    logger.warning(
                        f'Empty reference_id_path ({reference_id_path}) for code `{code}` in reference node {reference} with value {reference_id}'
                    )
                    continue

                if reference[1] == 'reference.utilizes':
                    if node_match.block_type in [
                        CodeBlockType.FUNCTION,
                        CodeBlockType.CLASS,
                    ]:
                        relationship_type = RelationshipType.DEFINED_BY
                    else:
                        relationship_type = RelationshipType.UTILIZES
                elif reference[1] == 'reference.provides':
                    relationship_type = RelationshipType.PROVIDES
                elif reference[1] == 'reference.calls':
                    relationship_type = RelationshipType.CALLS
                elif reference[1] == 'reference.type':
                    relationship_type = RelationshipType.IS_A
                else:
                    relationship_type = RelationshipType.USES

                references.append(
                    Relationship(
                        scope=ReferenceScope.LOCAL,
                        type=relationship_type,
                        identifier=identifier,
                        path=reference_id_path,
                    )
                )
        return references

    def create_parameters(self, content_bytes, node_match, references):
        parameters = []
        for parameter in node_match.parameters:
            parameter_type = (
                self.get_content(parameter[1], content_bytes) if parameter[1] else None
            )
            parameter_id = self.get_content(parameter[0], content_bytes)

            parameters.append(Parameter(identifier=parameter_id, type=parameter_type))

            if parameter_type:
                parameter_type = parameter_type.replace('"', '')

                type_split = parameter_type.split('.')

                reference = Relationship(
                    scope=ReferenceScope.LOCAL, identifier=parameter_id, path=type_split
                )
                references.append(reference)
        return parameters

    def add_to_index(self, codeblock: CodeBlock):
        if self.index_callback:
            self.index_callback(codeblock)

    def pre_process(self, codeblock: CodeBlock, node_match: NodeMatch):
        pass

    def post_process(self, codeblock: CodeBlock):
        pass

    def get_previous(self, node: Node, origin_node: Node):
        if node == origin_node:
            return node.start_byte
        if node.prev_sibling:
            return node.prev_sibling.end_byte
        elif node.parent:
            return self.get_previous(node.parent, origin_node)
        else:
            return node.start_byte

    def get_parent_next(self, node: Node, orig_node: Node):
        self.debug_log(f'get_parent_next: {node.type} - {orig_node.type}')
        if node != orig_node:
            if node.next_sibling:
                self.debug_log(
                    f'get_parent_next: node.next_sibling -> {node.next_sibling}'
                )
                return node.next_sibling
            else:
                return self.get_parent_next(node.parent, orig_node)
        return None

    def has_error(self, node: Node):
        if node.type == 'ERROR':
            return True
        if node.children:
            return any(self.has_error(child) for child in node.children)
        return False

    def parse(self, content, file_path: Optional[str] = None) -> Module:
        if isinstance(content, str):
            content_in_bytes = bytes(content, self.encoding)
        elif isinstance(content, bytes):
            content_in_bytes = content
        else:
            raise ValueError('Content must be either a string or bytes')

        # TODO: make thread safe?
        self.spans_by_id = {}
        self._span_counter = {}

        # TODO: Should me moved to a central CodeGraph
        self._graph = nx.DiGraph()

        tree = self.tree_parser.parse(content_in_bytes)
        # print(f'Parsed tree: {tree.root_node}')
        module, _, _ = self.parse_code(
            content_in_bytes, tree.walk().node, file_path=file_path
        )
        module.spans_by_id = self.spans_by_id
        module.file_path = file_path
        module.language = self.language
        module._graph = self._graph
        return module

    def get_content(self, node: Node, content_bytes: bytes) -> str:
        return content_bytes[node.start_byte : node.end_byte].decode(self.encoding)

    def _create_new_span(
        self, current_span: Optional[BlockSpan], block: CodeBlock
    ) -> Optional[BlockSpan]:
        # Set documentation phase on comments in the start of structure blocks if more than min_tokens_for_docs_span
        # TODO: This is isn't valid in other languages, try to set block type to docstring?
        block_types_with_document_span = [
            CodeBlockType.MODULE
        ]  # TODO: Make this configurable
        if block.type == CodeBlockType.COMMENT and (
            not current_span
            or current_span.block_type in block_types_with_document_span
            and (
                current_span.span_type != SpanType.IMPLEMENTATION
                or current_span.index == 0
            )
        ):
            span_type = SpanType.DOCUMENTATION
            span_id = self._create_span_id(block, label='docstring')

        # Set initation phase when block is a class or constructor, and until first function:
        elif block.type == CodeBlockType.CLASS or (
            current_span
            and current_span.block_type
            in [CodeBlockType.CLASS, CodeBlockType.CONSTRUCTOR]
            and current_span.initiating_block.parent != block.parent
            and current_span.span_type != SpanType.IMPLEMENTATION
            and block.type not in [CodeBlockType.FUNCTION]
        ):
            span_type = SpanType.INITATION
            span_id = self._create_span_id(block)

        # Set initation phase on imports in module blocks
        elif block.type == CodeBlockType.IMPORT and (
            not current_span or current_span.block_type == CodeBlockType.MODULE
        ):
            span_type = SpanType.INITATION
            span_id = self._create_span_id(block, label='imports')

        else:
            span_type = SpanType.IMPLEMENTATION
            span_id = self._create_span_id(block)

        # if no curent_span exists, expected to be on Module level
        if not current_span:
            if block.type.group == CodeBlockTypeGroup.STRUCTURE:
                return BlockSpan(
                    span_id=span_id,
                    span_type=span_type,
                    start_line=block.start_line,
                    end_line=block.start_line,
                    initiating_block=block,
                    parent_block_path=block.full_path(),
                )
            else:
                return BlockSpan(
                    span_id=span_id,
                    span_type=span_type,
                    start_line=block.start_line,
                    end_line=block.start_line,
                    initiating_block=block.parent,
                    parent_block_path=block.parent.full_path() if block.parent else [],
                )

        # create a new span on new functions and classes in classes or modules.
        # * if the parent block doesn't have a span
        if (
            block.type in [CodeBlockType.CLASS, CodeBlockType.FUNCTION]
            and block.parent
            and block.parent.type in [CodeBlockType.MODULE, CodeBlockType.CLASS]
            and current_span.parent_block_path == block.parent.full_path()
        ):
            if len(current_span.parent_block_path) < len(block.full_path()):
                # If there is a current span from the parent block it should be set to is_partial
                current_span.is_partial = True

            return BlockSpan(
                span_id=span_id,
                span_type=span_type,
                start_line=block.start_line,
                end_line=block.start_line,
                initiating_block=block,
                parent_block_path=block.full_path(),
            )

        # if current span is from a child block
        if len(current_span.parent_block_path) > len(
            block.parent.full_path() if block.parent else []
        ):
            if block.type.group == CodeBlockTypeGroup.STRUCTURE:
                parent_block_path = block.full_path()
            else:
                parent_block_path = block.parent.full_path() if block.parent else []

            return BlockSpan(
                span_id=span_id,
                span_type=span_type,
                start_line=block.start_line,
                end_line=block.start_line,
                initiating_block=block,
                parent_block_path=parent_block_path,
            )

        # Create new span if span type has changed
        if span_type != current_span.span_type:
            return BlockSpan(
                span_id=span_id,
                span_type=span_type,
                start_line=block.start_line,
                end_line=block.start_line,
                initiating_block=current_span.initiating_block,
                parent_block_path=current_span.parent_block_path,
            )

        # Create new span if the current is too large and the parent block is a structure block
        split_on_block_type = [CodeBlockType.MODULE]  # Only split on Module level
        if (
            current_span.tokens + block.sum_tokens() > self._max_tokens_in_span
            and block.parent
            and block.parent.type in split_on_block_type
        ):
            current_span.is_partial = True

            return BlockSpan(
                span_id=span_id,
                span_type=span_type,
                start_line=block.start_line,
                end_line=block.start_line,
                initiating_block=current_span.initiating_block,
                parent_block_path=current_span.parent_block_path,
                is_partial=True,
                index=current_span.index + 1,
            )

        return None

    def _create_span_id(self, block: CodeBlock, label: Optional[str] = None):
        structure_block: Optional[CodeBlock] = None
        if block.type.group == CodeBlockTypeGroup.STRUCTURE:
            structure_block = block
        else:
            structure_block = block.find_type_group_in_parents(
                CodeBlockTypeGroup.STRUCTURE
            )
            if not structure_block:
                raise ValueError(
                    f'Could not find structure block for block {block.path_string()}'
                )

        span_id = structure_block.path_string()
        if label and span_id:
            span_id += f':{label}'
        elif label and not span_id:
            span_id = label
        elif not span_id:
            span_id = 'impl'

        if span_id in self._span_counter:
            self._span_counter[span_id] += 1
            span_id += f':{self._span_counter[span_id]}'
        else:
            self._span_counter[span_id] = 1

        return span_id

    def _count_tokens(self, content: str):
        if not self.tokenizer:
            return 0
        return len(self.tokenizer(content))

    def debug_log(self, message: str):
        if self.debug:
            logger.debug(message)
