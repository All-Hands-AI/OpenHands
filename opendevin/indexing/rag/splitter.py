import logging
from typing import Any, Iterable, List, Sequence

from llama_index.core.node_parser import NodeParser, TextSplitter
from llama_index.core.schema import BaseNode
from llama_index.core.utils import get_tqdm_iterable
from pydantic import Field

from .codeblock.parser import PythonParser

logger = logging.getLogger(__name__)


class EpicSplitter(NodeParser):
    text_splitter: TextSplitter = Field(
        description='The text splitter to use for splitting the non-code documents into nodes'
    )

    include_non_code_files: bool = Field(
        default=True, description='Whether to include non-code files in the index'
    )

    non_code_file_extensions: List[str] = Field(
        default=['md', 'txt'],
        description='The extensions of the non-code files to include in the index',
    )

    chunk_size: int = Field(
        default=1500, description='Chunk size to use for splitting code documents.'
    )

    hard_token_limit: int = Field(
        default=6000, description='Hard token limit for a chunk.'
    )

    def __init__(self) -> None:
        # TODO:
        pass

    def _parse_nodes(
        self, nodes: Sequence[BaseNode], show_progress: bool = False, **kwargs: Any
    ) -> List[BaseNode]:
        nodes_with_progress: Iterable[BaseNode] = get_tqdm_iterable(
            nodes, show_progress, 'Parsing nodes'
        )

        all_nodes: List[BaseNode] = []

        for node in nodes_with_progress:
            file_path = node.metadata.get('file_path')
            content = node.get_content()

            try:
                parser = PythonParser()
                code_module = parser.parse(content, file_path)
            except Exception as e:
                print(f'Error parsing code block: {e}')
                # TODO: fall back to `CodeSplitter`
                continue

        chunks = self._chunk_code_block(code_module, file_path)
        logger.info(f'Splitting file {file_path} in {len(chunks)} chunks')

        for chunk in chunks:
            # TODO: construct nodes from chunks
            print(all_nodes)
            continue

        return []
