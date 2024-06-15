import logging
import re
from dataclasses import dataclass, field
from importlib.resources import open_text
from typing import Any, List, Optional, Tuple

import networkx as nx
from tree_sitter import Language, Node, Parser, Query

from ..codeblock import CodeBlock, CodeBlockSpan, CodeBlockType
from ..codemodule import CodeModule

logger = logging.getLogger(__name__)


@dataclass
class NodeMatchResult:
    block_type: Optional[CodeBlockType] = None  # The type of the code block
    identifier_node: Optional[Node] = None  # The identifier node
    first_child: Optional[Node] = None  # The first child node
    last_child: Optional[Node] = None  # The last child node
    check_child: Optional[Node] = None  # The child node to check
    parameters: List[Tuple[Node, Optional[Node]]] = field(
        default_factory=list
    )  # Parameters of the code block
    relationships: List[Tuple[Node, str]] = field(
        default_factory=list
    )  # `Reference` relationships between nodes


class CodeParser:
    def __init__(
        self, language: Language, encoding: str = 'utf8', max_tokens_in_span: int = 500
    ) -> None:
        try:
            self.tree_parser = Parser(language)
            self.tree_parser.set_language(language)
            self.parser_language = language
        except Exception as e:
            logger.error(f'Could not get parser for language {language}.')
            raise e

        self.encoding = encoding
        self._max_tokens_in_span = max_tokens_in_span
        self.queries: Any = []  # FIXME: add type

    def parse(
        self, content: str | bytes, file_path: Optional[str] = None
    ) -> CodeModule:
        if isinstance(content, str):
            content_in_bytes = content.encode(self.encoding)
        elif isinstance(content, bytes):
            content_in_bytes = content
        else:
            raise ValueError('content must be a string or bytes')

        self._graph = nx.DiGraph

        tree = self.tree_parser.parse(source_code=content_in_bytes)
        module, _, _ = self.parse_code(
            content_in_bytes, tree.walk().node, file_path=file_path
        )

        # TODO: add some properties to the module
        return module

    def parse_code(
        self, content_bytes: bytes, cur_node: Node, file_path: Optional[str] = None
    ) -> Tuple[CodeBlock, Node, CodeBlockSpan]:
        node_match = self.find_in_tree(node=cur_node)
        print(node_match)

        # TODO:

        raise NotImplementedError()

    def find_in_tree(self, node: Node) -> Optional[NodeMatchResult]:
        match = self.find_match(node)

        if match:
            logger.info(
                f'find_in_tree() Found match on node type {node.type} with block type {match.block_type}'
            )
            return match
        else:
            logger.info(
                f'find_in_tree() Found no match on node type {node.type} set block type {CodeBlockType.CODE}'
            )
            return NodeMatchResult(block_type=CodeBlockType.CODE)

    def find_match(self, node: Node) -> Optional[NodeMatchResult]:
        for query_label, node_type, query in self.queries:
            if node_type and node.type != node_type and node_type != '_':
                continue

            match = self._find_match(node, query, query_label)
            if match:
                logger.info(
                    f'find_match() Found match on node {node.type} with query {query_label}'
                )
                return match

        return None

    def _find_match(
        self, node: Node, query: Query, query_label: str
    ) -> Optional[NodeMatchResult]:
        captures = query.captures(node)
        match_result: NodeMatchResult = NodeMatchResult()

        if not captures:
            return None

        root_node = None
        for found_node, tag in captures:
            logger.info(f'[{query_label}] Found tag {tag} on node {found_node}')

            # Root node is the first node that matches the root tag
            if tag == 'root' and not root_node and node == found_node:
                logger.info(f'[{query_label}] Root node {found_node}')
                root_node = found_node

            if not root_node:
                # Skip if the root node is not found yet
                continue

            if tag == 'no_children' and found_node.children:
                return None

            if tag == 'check_child':
                logger.info(f'[{query}] Check child {found_node}')
                check_match_result = self.find_match(found_node)
                if check_match_result:
                    check_match_result.check_child = found_node
                return check_match_result

            if tag == 'parse_child':
                logger.info(f'[{query_label}] Parse child {found_node}')

                child_match_result = self.find_match(found_node)
                if child_match_result:
                    if child_match_result.relationships:
                        logger.info(
                            f'[{query_label}] Found {len(child_match_result.relationships)} references on child {found_node}'
                        )
                        match_result.relationships = child_match_result.relationships
                    if child_match_result.parameters:
                        logger.info(
                            f'[{query_label}] Found {len(child_match_result.parameters)} parameters on child {found_node}'
                        )
                        match_result.parameters.extend(child_match_result.parameters)
                    if child_match_result.first_child:
                        logger.info(
                            f'[{query_label}] Found first child on child {found_node}'
                        )
                        match_result.first_child = child_match_result.first_child

            if tag == 'identifier' and not match_result.identifier_node:
                match_result.identifier_node = found_node

            if tag == 'child.first' and not match_result.first_child:
                match_result.first_child = found_node

            if tag == 'child.last':
                match_result.last_child = found_node

            if tag == 'parameter.identifier':
                match_result.parameters.append((found_node, None))

            if tag == 'parameter.type':
                match_result.parameters[-1] = (
                    match_result.parameters[-1][0],
                    found_node,
                )

            if root_node and tag.startswith('reference'):
                match_result.relationships.append((found_node, tag))

            if not match_result.block_type:
                match_result.block_type = CodeBlockType.from_str(tag)

        if match_result.block_type:
            logger.info(
                f'[{query_label}] Return match with type {match_result.block_type} for node {node}'
            )
            return match_result

        return None

    def _build_queries(self, query_file: str):
        """
        Builds and parses queries from a query file.

        Args:
            query_file (str): The path to the query file.

        Returns:
            list: A list of parsed queries, each containing the query label, node type, and parsed query.
        """
        with open_text(
            'opendevin.indexing.rag.codeblock.parser.queries', query_file
        ) as f:
            query_list = f.read().strip().split('\n\n')
            parsed_queries = []

            for i, query in enumerate(query_list):
                node_type = self._extract_node_type(query)
                parsed_queries.append(
                    (
                        f'{query_file}:{i+1}',
                        node_type,
                        self.parser_language.query(query),
                    )
                )

            return parsed_queries

    def _extract_node_type(self, query: str) -> str:
        """
        Extracts the node type from the given query, by parsing the first word after an opening parenthesis.

        Args:
            query (str): The query string.

        Returns:
            str: The extracted node type.

        Raises:
            ValueError: If the query cannot be parsed.
        """
        pattern = r'\(\s*(\w+)'
        match = re.match(pattern, query)

        if match:
            return match.group(1)
        else:
            logger.error(f'Could not parse query: {query}')
            raise ValueError(f'Could not parse query: {query}')
