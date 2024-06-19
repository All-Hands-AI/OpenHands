import re
import time
from typing import Any, Callable, List, Optional, Sequence

from llama_index.core.bridge.pydantic import Field
from llama_index.core.callbacks import CallbackManager
from llama_index.core.node_parser import NodeParser, TextSplitter, TokenTextSplitter

# from llama_index.core.node_parser.node_utils import logger
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.utils import get_tokenizer, get_tqdm_iterable

from opendevin.core.logger import opendevin_logger as logger

from ..codeblocks.codeblocks import CodeBlock, CodeBlockType, PathTree
from ..codeblocks.parser.python import PythonParser
from ..index.code_node import CodeNode
from ..index.settings import CommentStrategy

CodeBlockChunk = List[CodeBlock]


def count_chunk_tokens(chunk: CodeBlockChunk) -> int:
    return sum([block.tokens for block in chunk])


def count_parent_tokens(codeblock: CodeBlock) -> int:
    tokens = codeblock.tokens
    if codeblock.parent:
        tokens += codeblock.parent.tokens
    return tokens


SPLIT_BLOCK_TYPES = [
    CodeBlockType.FUNCTION,
    CodeBlockType.CLASS,
    CodeBlockType.TEST_SUITE,
    CodeBlockType.TEST_CASE,
    CodeBlockType.MODULE,
]


class EpicSplitter(NodeParser):
    text_splitter: TextSplitter = Field(
        description='Text splitter to use for splitting non code documents into nodes.'
    )

    include_non_code_files: bool = Field(
        default=True, description='Whether or not to include non code files.'
    )

    non_code_file_extensions: List[str] = Field(
        default=['md', 'txt'],
        description='File extensions to consider as non code files.',
    )

    comment_strategy: CommentStrategy = Field(
        default=CommentStrategy.INCLUDE, description='Comment strategy to use.'
    )

    chunk_size: int = Field(
        default=1500, description='Chunk size to use for splitting code documents.'
    )

    max_chunks: int = Field(
        default=100, description='Max number of chunks to split a document into.'
    )

    min_chunk_size: int = Field(default=256, description='Min tokens to split code.')

    max_chunk_size: int = Field(default=2000, description='Max tokens in one chunk.')

    hard_token_limit: int = Field(
        default=6000, description='Hard token limit for a chunk.'
    )

    repo_path: str = Field(default=None, description='Path to the repository.')

    index_callback: Optional[Callable] = Field(
        default=None, description='Callback to call when indexing a code block.'
    )

    # _fallback_code_splitter: Optional[TextSplitter] = PrivateAttr() TODO: Implement fallback when tree sitter fails

    def __init__(
        self,
        chunk_size: int = 750,
        min_chunk_size: int = 100,
        max_chunk_size: int = 1500,
        hard_token_limit: int = 6000,
        max_chunks: int = 100,
        include_metadata: bool = True,
        include_prev_next_rel: bool = True,
        text_splitter: Optional[TextSplitter] = None,
        index_callback: Optional[Callable[[CodeBlock], None]] = None,
        repo_path: Optional[str] = None,
        comment_strategy: CommentStrategy = CommentStrategy.ASSOCIATE,
        # fallback_code_splitter: Optional[TextSplitter] = None,
        include_non_code_files: bool = True,
        tokenizer: Optional[Callable] = None,
        non_code_file_extensions: Optional[List[str]] = None,
        callback_manager: Optional[CallbackManager] = None,
    ) -> None:
        callback_manager = callback_manager or CallbackManager([])

        # self._fallback_code_splitter = fallback_code_splitter

        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=0,
            text_splitter=text_splitter or TokenTextSplitter(),
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
            hard_token_limit=hard_token_limit,
            max_chunks=max_chunks,
            index_callback=index_callback,
            repo_path=repo_path,
            comment_strategy=comment_strategy,
            include_non_code_files=include_non_code_files,
            non_code_file_extensions=non_code_file_extensions or ['md', 'txt'],
            include_metadata=include_metadata,
            include_prev_next_rel=include_prev_next_rel,
            callback_manager=callback_manager,
        )

    @classmethod
    def class_name(cls):
        return 'GhostcoderNodeParser'

    def _parse_nodes(
        self,
        nodes: Sequence[BaseNode],
        show_progress: bool = False,
        **kwargs: Any,
    ) -> List[BaseNode]:
        nodes_with_progress = get_tqdm_iterable(nodes, show_progress, 'Parsing nodes')

        all_nodes: List[BaseNode] = []

        for node in nodes_with_progress:
            file_path = node.metadata.get('file_path')
            content = node.get_content()
            # logger.info('Content: ' + content + '...' + 'Length: ' + str(len(content)))

            try:
                # TODO: Derive language from file extension
                starttime = time.time_ns()

                parser = PythonParser(index_callback=self.index_callback)
                codeblock = parser.parse(content, file_path=file_path)

                parse_time = time.time_ns() - starttime
                if parse_time > 1e9:
                    logger.warning(
                        f'Parsing file {file_path} took {parse_time / 1e9:.2f} seconds.'
                    )

            except Exception as e:
                logger.warning(
                    f'Failed to use epic splitter to split {file_path}. Fallback to treesitter_split(). Error: {e}'
                )
                # TODO: Fall back to treesitter or text split
                continue

            starttime = time.time_ns()
            chunks = self._chunk_contents(codeblock=codeblock, file_path=file_path)
            parse_time = time.time_ns() - starttime
            if parse_time > 1e8:
                logger.warning(
                    f'Splitting file {file_path} took {parse_time / 1e9:.2f} seconds.'
                )
            if len(chunks) > 100:
                logger.info(f'Splitting file {file_path} in {len(chunks)} chunks')

            starttime = time.time_ns()
            for chunk in chunks:
                path_tree = self._create_path_tree(chunk)
                content = self._to_context_string(codeblock, path_tree)
                chunk_node = self._create_node(content, node, chunk=chunk)
                if chunk_node:
                    all_nodes.append(chunk_node)
            parse_time = time.time_ns() - starttime
            if parse_time > 1e9:
                logger.warning(
                    f'Create nodes for file {file_path} took {parse_time / 1e9:.2f} seconds.'
                )
        return all_nodes

    def _chunk_contents(
        self, codeblock: Optional[CodeBlock] = None, file_path: Optional[str] = None
    ) -> List[CodeBlockChunk]:
        if not codeblock:
            return []

        tokens = codeblock.sum_tokens()
        if tokens == 0:
            logger.debug(f'Skipping file {file_path} because it has no tokens.')
            return []

        if codeblock.find_errors():
            logger.warning(
                f'Failed to use spic splitter to split {file_path}. {len(codeblock.find_errors())} codeblocks with type ERROR. Fallback to treesitter_split()'
            )
            # TODO: Fall back to treesitter or text split
            return []

        if tokens > self.hard_token_limit:
            for child in codeblock.children:
                if (
                    child.type == CodeBlockType.COMMENT
                    and 'generated' in child.content.lower()
                ):  # TODO: Make a generic solution to detect files that shouldn't be indexed. Maybe ask an LLM?
                    logger.info(
                        f"File {file_path} has {tokens} tokens and the word 'generated' in the first comments,"
                        f" will assume it's a generated file."
                    )
                    return []
                else:
                    break

        if tokens < self.min_chunk_size:
            child_blocks = codeblock.get_all_child_blocks()
            return [[codeblock] + child_blocks]

        return self._chunk_block(codeblock, file_path)

    def _chunk_block(
        self, codeblock: CodeBlock, file_path: Optional[str] = None
    ) -> list[CodeBlockChunk]:
        chunks: List[CodeBlockChunk] = []
        current_chunk: Any = []
        comment_chunk: Any = []

        parent_tokens = count_parent_tokens(codeblock)

        ignoring_comment = False

        for child in codeblock.children:
            if child.type == CodeBlockType.COMMENT:
                if self.comment_strategy == CommentStrategy.EXCLUDE:
                    continue
                elif self._ignore_comment(child) or ignoring_comment:
                    ignoring_comment = True
                    continue
                elif (
                    self.comment_strategy == CommentStrategy.ASSOCIATE
                    and not codeblock.parent
                ):
                    comment_chunk.append(child)
                    continue
            else:
                if child.tokens > self.max_chunk_size:
                    start_content = child.content[:100]
                    logger.warning(
                        f'Skipping code block {child.path_string()} in {file_path} as it has {child.tokens} tokens which is'
                        f' more than chunk size {self.chunk_size}. Content: {start_content}...'
                    )
                    continue

                ignoring_comment = False

            if (
                child.type in SPLIT_BLOCK_TYPES
                and child.sum_tokens() > self.min_chunk_size
            ) or parent_tokens + child.sum_tokens() > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []

                current_chunk.extend(comment_chunk)
                comment_chunk = []
                current_chunk.append(child)

                child_chunks = self._chunk_block(child, file_path=file_path)

                if child_chunks:
                    first_child_chunk = child_chunks[0]

                    if (
                        parent_tokens
                        + child.tokens
                        + count_chunk_tokens(first_child_chunk)
                        < self.max_chunk_size
                    ):
                        current_chunk.extend(first_child_chunk)
                        chunks.append(current_chunk)
                        chunks.extend(child_chunks[1:])
                        current_chunk = []
                    else:
                        chunks.append(current_chunk)
                        chunks.extend(child_chunks)
                        current_chunk = []

                continue

            new_token_count = (
                parent_tokens + count_chunk_tokens(current_chunk) + child.sum_tokens()
            )
            if (
                codeblock.type not in SPLIT_BLOCK_TYPES
                and new_token_count < self.max_chunk_size
                or new_token_count < self.chunk_size
            ):
                current_chunk.extend(comment_chunk)
                current_chunk.append(child)
            else:
                if current_chunk:
                    current_chunk.extend(comment_chunk)
                    chunks.append(current_chunk)
                current_chunk = [child]

            comment_chunk = []
            child_blocks = child.get_all_child_blocks()
            current_chunk.extend(child_blocks)

        if chunks and count_chunk_tokens(current_chunk) < self.min_chunk_size:
            chunks[-1].extend(current_chunk)
        else:
            chunks.append(current_chunk)

        return self._merge_chunks(chunks)

    def _merge_chunks(self, chunks: List[CodeBlockChunk]) -> List[CodeBlockChunk]:
        while True:
            merged_chunks = []
            should_continue = False

            for i, chunk in enumerate(chunks):
                if (
                    count_chunk_tokens(chunk) < self.min_chunk_size
                    or len(chunks) > self.max_chunks
                ):
                    if i == 0 and len(chunks) > 1:
                        if (
                            count_chunk_tokens(chunks[1]) + count_chunk_tokens(chunk)
                            <= self.hard_token_limit
                        ):
                            chunks[1] = chunk + chunks[1]
                            should_continue = True
                        else:
                            merged_chunks.append(chunk)

                    elif i == len(chunks) - 1:
                        if (
                            merged_chunks
                            and count_chunk_tokens(merged_chunks[-1])
                            + count_chunk_tokens(chunk)
                            <= self.hard_token_limit
                        ):
                            merged_chunks[-1] = merged_chunks[-1] + chunk
                            should_continue = True
                        else:
                            merged_chunks.append(chunk)

                    else:
                        if count_chunk_tokens(chunks[i - 1]) < count_chunk_tokens(
                            chunks[i + 1]
                        ):
                            if (
                                merged_chunks
                                and count_chunk_tokens(merged_chunks[-1])
                                + count_chunk_tokens(chunk)
                                <= self.hard_token_limit
                            ):
                                merged_chunks[-1] = merged_chunks[-1] + chunk
                                should_continue = True
                            else:
                                merged_chunks.append(chunk)
                        else:
                            if (
                                count_chunk_tokens(chunks[i + 1])
                                + count_chunk_tokens(chunk)
                                <= self.hard_token_limit
                            ):
                                chunks[i + 1] = chunk + chunks[i + 1]
                                should_continue = True
                            else:
                                merged_chunks.append(chunk)
                else:
                    merged_chunks.append(chunk)

            chunks = merged_chunks + chunks[i + 1 :]

            if len(chunks) < self.max_chunks or not should_continue:
                break

        return chunks

    def _create_path_tree(cls, blocks: List[CodeBlock]) -> PathTree:
        path_tree = PathTree()
        for block in blocks:
            path_tree.add_to_tree(block.full_path())
        return path_tree

    def _ignore_comment(self, codeblock: CodeBlock) -> bool:
        return (
            bool(re.search(r'(?i)copyright|license|author', codeblock.content))
            or not codeblock.content
        )

    def _to_context_string(self, codeblock: CodeBlock, path_tree: PathTree) -> str:
        contents = ''

        if codeblock.pre_lines:
            contents += '\n' * (codeblock.pre_lines - 1)
            for i, line in enumerate(codeblock.content_lines):
                if i == 0 and line:
                    contents += '\n' + codeblock.indentation + line
                elif line:
                    contents += '\n' + line
                else:
                    contents += '\n'
        else:
            contents += codeblock.pre_code + codeblock.content

        has_outcommented_code = False
        for i, child in enumerate(codeblock.children):
            child_tree = path_tree.child_tree(child.identifier)
            if child_tree and child_tree.show:
                if has_outcommented_code and child.type not in [
                    CodeBlockType.COMMENT,
                    CodeBlockType.COMMENTED_OUT_CODE,
                ]:
                    if codeblock.type not in [
                        CodeBlockType.CLASS,
                        CodeBlockType.MODULE,
                        CodeBlockType.TEST_SUITE,
                    ]:
                        contents += child.create_commented_out_block(
                            '... other code'
                        ).to_string()
                contents += self._to_context_string(
                    codeblock=child, path_tree=child_tree
                )
                has_outcommented_code = False
            elif child_tree:
                contents += self._to_context_string(
                    codeblock=child, path_tree=child_tree
                )
                has_outcommented_code = False
            elif child.type not in [
                CodeBlockType.COMMENT,
                CodeBlockType.COMMENTED_OUT_CODE,
            ]:
                has_outcommented_code = True

        if has_outcommented_code and codeblock.type not in [
            CodeBlockType.CLASS,
            CodeBlockType.MODULE,
            CodeBlockType.TEST_SUITE,
        ]:
            contents += child.create_commented_out_block('... other code').to_string()

        return contents

    def _contains_block_paths(self, codeblock: CodeBlock, block_paths: List[List[str]]):
        return [
            block_path
            for block_path in block_paths
            if block_path[: len(codeblock.full_path())] == codeblock.full_path()
        ]

    def _create_node(
        self, content: str, node: BaseNode, chunk: Optional[CodeBlockChunk] = None
    ) -> Optional[TextNode]:
        metadata = {}
        metadata.update(node.metadata)

        node_id = node.id_

        if chunk:
            metadata['start_line'] = chunk[0].start_line
            metadata['end_line'] = chunk[-1].end_line

            # TODO: Change this when EpicSplitter is adjusted to use the span concept natively
            span_ids = set(
                [
                    block.belongs_to_span.span_id
                    for block in chunk
                    if block.belongs_to_span
                ]
            )
            metadata['span_ids'] = list(span_ids)

            node_id += f'_{chunk[0].path_string()}_{chunk[-1].path_string()}'

        content = content.strip('\n')

        tokens = get_tokenizer()(content)
        metadata['tokens'] = len(tokens)

        excluded_embed_metadata_keys = node.excluded_embed_metadata_keys.copy()
        excluded_embed_metadata_keys.extend(['start_line', 'end_line', 'tokens'])

        return CodeNode(
            id_=node_id,
            text=content,
            metadata=metadata,
            excluded_embed_metadata_keys=excluded_embed_metadata_keys,
            excluded_llm_metadata_keys=node.excluded_llm_metadata_keys,
            metadata_seperator=node.metadata_seperator,
            metadata_template=node.metadata_template,
            text_template=node.text_template,
            # relationships={NodeRelationship.SOURCE: node.as_related_node_info()},
        )

    def _count_tokens(self, text: str):
        tokenizer = get_tokenizer()
        return len(tokenizer(text))
