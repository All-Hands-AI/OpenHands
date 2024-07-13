import fnmatch
import json
import mimetypes
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional

import requests
from llama_index.core import SimpleDirectoryReader
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.storage import docstore
from llama_index.core.storage.docstore import DocumentStore, SimpleDocumentStore
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    FilterCondition,
    MetadataFilter,
    MetadataFilters,
    VectorStoreQuery,
)
from rapidfuzz import fuzz

from opendevin.core.logger import opendevin_logger as logger
from opendevin.indexing.rag.embedding import get_embedding_model

from ..codeblocks import CodeBlock, CodeBlockType
from ..index.epic_split import EpicSplitter
from ..index.settings import IndexSettings
from ..index.simple_faiss import SimpleFaissVectorStore
from ..index.types import (
    CodeSnippet,
    SearchCodeHit,
    SearchCodeResponse,
)
from ..repository import FileRepository
from ..types import FileWithSpans
from ..utils.tokenizer import count_tokens
from .settings import MoatlessIndexSettings


def default_vector_store(settings: IndexSettings):
    try:
        import faiss
    except ImportError:
        raise ImportError(
            "faiss needs to be installed to set up a default index for CodeIndex. Run 'pip install faiss-cpu'"
        )

    faiss_index = faiss.IndexIDMap(faiss.IndexFlatL2(settings.embedding_dimensions))
    return SimpleFaissVectorStore(faiss_index)


class CodeIndex:
    def __init__(
        self,
        file_repo: FileRepository,
        vector_store: Optional[BasePydanticVectorStore] = None,
        docstore: Optional[DocumentStore] = None,
        embed_model: Optional[BaseEmbedding] = None,
        blocks_by_class_name: Optional[dict] = None,
        blocks_by_function_name: Optional[dict] = None,
        settings: Optional[MoatlessIndexSettings] = None,
    ):
        self._settings = settings or MoatlessIndexSettings()
        self._file_repo = file_repo

        self._blocks_by_class_name = blocks_by_class_name or {}
        self._blocks_by_function_name = blocks_by_function_name or {}

        self._embed_model = embed_model or get_embedding_model(
            self._settings.embedding_model_provider,
            self._settings.embedding_model_name,
        )
        print(self._embed_model)
        self._vector_store = vector_store or default_vector_store(self._settings)
        self._docstore = docstore or SimpleDocumentStore()

    @classmethod
    def from_persist_dir(cls, persist_dir: str, file_repo: FileRepository):
        vector_store = SimpleFaissVectorStore.from_persist_dir(persist_dir)
        docstore = SimpleDocumentStore.from_persist_dir(persist_dir)

        settings = MoatlessIndexSettings.from_persist_dir(persist_dir)

        if os.path.exists(os.path.join(persist_dir, 'blocks_by_class_name.json')):
            with open(os.path.join(persist_dir, 'blocks_by_class_name.json'), 'r') as f:
                blocks_by_class_name = json.load(f)
        else:
            blocks_by_class_name = {}

        if os.path.exists(os.path.join(persist_dir, 'blocks_by_function_name.json')):
            with open(
                os.path.join(persist_dir, 'blocks_by_function_name.json'), 'r'
            ) as f:
                blocks_by_function_name = json.load(f)
        else:
            blocks_by_function_name = {}

        return cls(
            file_repo=file_repo,
            vector_store=vector_store,
            docstore=docstore,
            settings=settings,
            blocks_by_class_name=blocks_by_class_name,
            blocks_by_function_name=blocks_by_function_name,
        )

    @classmethod
    def from_url(cls, url: str, persist_dir: str, file_repo: FileRepository):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_zip_file = os.path.join(temp_dir, url.split('/')[-1])

                with open(temp_zip_file, 'wb') as data:
                    for chunk in response.iter_content(chunk_size=8192):
                        data.write(chunk)

                shutil.unpack_archive(temp_zip_file, persist_dir)

        except requests.exceptions.HTTPError as e:
            logger.exception(f'HTTP Error while fetching {url}')
            raise e
        except Exception as e:
            logger.exception(f'Failed to download {url}')
            raise e

        logger.info(f'Downloaded existing index from {url}.')

        vector_store = SimpleFaissVectorStore.from_persist_dir(persist_dir)
        docstore = SimpleDocumentStore.from_persist_dir(persist_dir)

        if not os.path.exists(os.path.join(persist_dir, 'settings.json')):
            # TODO: Remove this when new indexes are uploaded
            settings = IndexSettings(embed_model='voyage-code-2')
        else:
            settings = IndexSettings.from_persist_dir(persist_dir)

        return cls(
            file_repo=file_repo,
            vector_store=vector_store,
            docstore=docstore,
            settings=settings,
        )

    def search(
        self,
        query: Optional[str] = None,
        code_snippet: Optional[str] = None,
        class_name: Optional[str] = None,
        function_name: Optional[str] = None,
        file_pattern: Optional[str] = None,
    ) -> SearchCodeResponse:
        if query or code_snippet:
            return self.semantic_search(
                query=query,
                code_snippet=code_snippet,
                class_name=class_name,
                function_name=function_name,
                file_pattern=file_pattern,
            )
        else:
            return self.find_by_name(
                class_name=class_name,
                function_name=function_name,
                file_pattern=file_pattern,
            )

    def semantic_search(
        self,
        query: Optional[str] = None,
        code_snippet: Optional[str] = None,
        class_name: Optional[str] = None,
        function_name: Optional[str] = None,
        file_pattern: Optional[str] = None,
        max_results: int = 25,
        max_hits_without_exact_match: int = 100,
        max_exact_results: int = 5,
    ) -> SearchCodeResponse:
        span_keywords = []
        if class_name:
            span_keywords.append(class_name)

        if function_name:
            span_keywords.append(function_name)

        content_keywords = [code_snippet] if code_snippet else None

        search_results = self._vector_search(
            query or '',
            file_pattern=file_pattern,
            span_keywords=span_keywords,
            content_keywords=content_keywords,
        )

        files_with_spans: dict[str, SearchCodeHit] = {}

        span_count = 0
        spans_with_exact_query_match = 0

        require_exact_query_match = False
        logger.info(f'search_results {len(search_results)}.')

        for rank, search_hit in enumerate(search_results):
            file = self._file_repo.get_file(search_hit.file_path)
            spans = []

            for span_id in search_hit.span_ids:
                span = file.module.find_span_by_id(span_id)

                if span:
                    spans.append(span)
                else:
                    logger.info(
                        f'Could not find span with id {span_id} in file {file.file_path}'
                    )

                    spans_by_line_number = file.module.find_spans_by_line_numbers(
                        search_hit.start_line, search_hit.end_line
                    )

                    for span_by_line_number in spans_by_line_number:
                        spans.append(span_by_line_number)

            for span in spans:
                has_exact_query_match = query and span.initiating_block.has_content(
                    query, span.span_id
                )

                span_count += 1
                if has_exact_query_match:
                    spans_with_exact_query_match += 1

                if has_exact_query_match and not require_exact_query_match:
                    require_exact_query_match = True
                    files_with_spans = {}

                if (
                    not require_exact_query_match and span_count <= max_results
                ) or has_exact_query_match:
                    if search_hit.file_path not in files_with_spans:
                        files_with_spans[search_hit.file_path] = SearchCodeHit(
                            file_path=search_hit.file_path
                        )

                    if files_with_spans[search_hit.file_path].contains_span(
                        span.span_id
                    ):
                        continue

                    files_with_spans[search_hit.file_path].add_span(
                        span_id=span.span_id, rank=rank
                    )

            span_count = sum([len(file.spans) for file in files_with_spans.values()])

            if spans_with_exact_query_match > max_exact_results or (
                spans_with_exact_query_match == 0
                and span_count > max_hits_without_exact_match
            ):
                break

        if require_exact_query_match:
            logger.info(
                f'semantic_search() Found {spans_with_exact_query_match} code spans with exact match out of {span_count} spans..'
            )
            message = f'Found {spans_with_exact_query_match} code spans with code that matches the exact query `{query}`.'
        else:
            logger.info(f'semantic_search() Found {span_count} code spans.')
            message = f'Found {span_count} code spans.'

        return SearchCodeResponse(message=message, hits=list(files_with_spans.values()))

    def find_by_name(
        self,
        class_name: Optional[str] = None,
        function_name: Optional[str] = None,
        file_pattern: Optional[str] = None,
        category: str = 'implementation',
    ) -> SearchCodeResponse:
        if not class_name and not function_name:
            raise ValueError(
                'At least one of class_name or function_name must be provided.'
            )

        if function_name:
            paths = self._blocks_by_function_name.get(function_name, [])
        else:
            paths = self._blocks_by_class_name.get(class_name, [])

        logger.info(
            f'find_by_name(class_name={class_name}, function_name={function_name}, file_pattern={file_pattern}) {len(paths)} hits.'
        )

        if not paths:
            if function_name:
                return SearchCodeResponse(
                    message=f'No functions found with the name {function_name}.'
                )
            else:
                return SearchCodeResponse(
                    message=f'No classes found with the name {class_name}.'
                )

        if category != 'test':
            exclude_files = self._file_repo.matching_files('**/test*/**')

            filtered_paths = []
            for file_path, block_path in paths:
                if file_path not in exclude_files:
                    filtered_paths.append((file_path, block_path))

            filtered_out_test_files = len(paths) - len(filtered_paths)
            if filtered_out_test_files > 0:
                logger.info(
                    f'find_by_name() Filtered out {filtered_out_test_files} test files.'
                )

            paths = filtered_paths

        check_all_files = False
        if file_pattern:
            include_files = self._file_repo.matching_files(file_pattern)

            if include_files:
                filtered_paths = []
                for file_path, block_path in paths:
                    if file_path in include_files:
                        filtered_paths.append((file_path, block_path))

                filtered_out_by_file_pattern = len(paths) - len(filtered_paths)
                if filtered_paths:
                    logger.info(
                        f'find_by_name() Filtered out {filtered_out_by_file_pattern} files by file pattern.'
                    )
                    paths = filtered_paths
                else:
                    logger.info(
                        f'find_by_name() No files found for file pattern {file_pattern}. Will search all files...'
                    )
                    check_all_files = True

        filtered_out_by_class_name = 0
        invalid_blocks = 0

        files_with_spans = {}
        for file_path, block_path in paths:
            file = self._file_repo.get_file(file_path)
            block = file.module.find_by_path(block_path)

            if not block:
                invalid_blocks += 1
                continue

            if class_name and function_name:
                parent_class = block.find_type_in_parents(CodeBlockType.CLASS)
                if not parent_class or parent_class.identifier != class_name:
                    filtered_out_by_class_name += 1
                    continue

            if file_path not in files_with_spans:
                files_with_spans[file_path] = FileWithSpans(file_path=file_path)

            files_with_spans[file_path].add_span_id(block.belongs_to_span.span_id)
            if not function_name:
                for child in block.children:
                    if (
                        child.belongs_to_span.span_id
                        not in files_with_spans[file_path].span_ids
                    ):
                        files_with_spans[file_path].add_span_id(
                            child.belongs_to_span.span_id
                        )

        if filtered_out_by_class_name > 0:
            logger.info(
                f'find_by_function_name() Filtered out {filtered_out_by_class_name} functions by class name {class_name}.'
            )

        if invalid_blocks > 0:
            logger.info(
                f'find_by_function_name() Ignored {invalid_blocks} invalid blocks.'
            )

        if check_all_files:
            message = f"The provided file pattern didn't match any files. But I found {len(files_with_spans)} matches in other files."

        else:
            message = f'Found {len(files_with_spans)} hits.'

        file_paths = [file.file_path for file in files_with_spans.values()]
        if file_pattern:
            file_paths = _rerank_files(file_paths, file_pattern)

        search_hits = []
        for rank, file_path in enumerate(file_paths):
            file = files_with_spans[file_path]
            search_hits.append(self._create_search_hit(file, rank))

        return SearchCodeResponse(
            message=message,
            hits=search_hits,
        )

    def _create_search_hit(self, file: FileWithSpans, rank: int = 0):
        file_hit = SearchCodeHit(file_path=file.file_path)
        for span_id in file.span_ids:
            file_hit.add_span(span_id, rank)
        return file_hit

    def _vector_search(
        self,
        query: str = '',
        exact_query_match: bool = False,
        category: str = 'implementation',
        file_pattern: Optional[str] = None,
        span_keywords: Optional[List[str]] = None,
        content_keywords: Optional[List[str]] = None,
    ):
        if file_pattern:
            query += f' file:{file_pattern}'

        if span_keywords:
            query += ', '.join(span_keywords)

        if content_keywords:
            query += ', '.join(content_keywords)

        if not query:
            raise ValueError(
                'At least one of query, span_keywords or content_keywords must be provided.'
            )

        query_embedding = self._embed_model.get_query_embedding(query)

        filters = MetadataFilters(filters=[], condition=FilterCondition.AND)
        if category:
            filters.filters.append(MetadataFilter(key='category', value=category))

        query_bundle = VectorStoreQuery(
            query_str=query,
            query_embedding=query_embedding,
            similarity_top_k=500,  # TODO: Fix paging?
            filters=filters,
        )

        result = self._vector_store.query(query_bundle)

        filtered_out_snippets = 0
        ignored_removed_snippets = 0
        sum_tokens = 0

        sum_tokens_per_file = {}

        if file_pattern:
            include_files = self._file_repo.matching_files(file_pattern)
            if len(include_files) == 0:
                logger.info(
                    f'find_code() No files found for file pattern {file_pattern}, will search all files...'
                )
                include_files = []

        else:
            include_files = []

        if category != 'test':
            exclude_files = self._file_repo.find_files(
                ['**/tests/**', 'tests*', '*_test.py', 'test_*.py']
            )
        else:
            exclude_files = set()

        search_results = []

        for node_id, distance in zip(result.ids, result.similarities):
            node_doc = self._docstore.get_document(node_id, raise_error=False)
            if not node_doc:
                ignored_removed_snippets += 1
                # TODO: Retry to get top_k results
                continue

            if exclude_files and node_doc.metadata['file_path'] in exclude_files:
                filtered_out_snippets += 1
                continue

            if include_files and node_doc.metadata['file_path'] not in include_files:
                filtered_out_snippets += 1
                continue

            if exact_query_match and query not in node_doc.get_content():
                filtered_out_snippets += 1
                continue

            span_ids = node_doc.metadata.get('span_ids', [])
            if span_keywords:
                if not any(
                    any(keyword in span_id for keyword in span_keywords)
                    for span_id in span_ids
                ):
                    filtered_out_snippets += 1
                    continue

            if content_keywords:
                if not any(
                    keyword in node_doc.get_content() for keyword in content_keywords
                ):
                    filtered_out_snippets += 1
                    continue

            if node_doc.metadata['file_path'] not in sum_tokens_per_file:
                sum_tokens_per_file[node_doc.metadata['file_path']] = 0

            sum_tokens += node_doc.metadata['tokens']
            sum_tokens_per_file[node_doc.metadata['file_path']] += node_doc.metadata[
                'tokens'
            ]

            code_snippet = CodeSnippet(
                id=node_doc.id_,
                file_path=node_doc.metadata['file_path'],
                distance=distance,
                content=node_doc.get_content(),
                tokens=node_doc.metadata['tokens'],
                span_ids=span_ids,
                start_line=node_doc.metadata.get('start_line', None),
                end_line=node_doc.metadata.get('end_line', None),
            )

            search_results.append(code_snippet)

        # TODO: Rerank by file pattern if no exact matches on file pattern

        logger.info(
            f'_vector_search() Found {len(search_results)} search results. '
            f'Ignored {ignored_removed_snippets} removed search results. '
            f'Filtered out {filtered_out_snippets} search results.'
        )

        return search_results

    def run_ingestion(
        self,
        repo_path: Optional[str] = None,
        input_files: Optional[list[str]] = None,
        num_workers: Optional[int] = None,
    ):
        repo_path = repo_path or self._file_repo.path

        # Only extract file name and type to not trigger unnecessary embedding jobs
        def file_metadata_func(file_path: str) -> Dict:
            file_path = file_path.replace(repo_path, '')
            if file_path.startswith('/'):
                file_path = file_path[1:]

            test_patterns = [
                '**/test/**',
                '**/tests/**',
                '**/test_*.py',
                '**/*_test.py',
            ]
            category = (
                'test'
                if any(fnmatch.fnmatch(file_path, pattern) for pattern in test_patterns)
                else 'implementation'
            )

            return {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_type': mimetypes.guess_type(file_path)[0],
                'category': category,
            }

        reader = SimpleDirectoryReader(
            input_dir=repo_path,
            file_metadata=file_metadata_func,
            input_files=input_files,
            filename_as_id=True,
            required_exts=['.py'],  # TODO: Shouldn't be hardcoded and filtered
            recursive=True,
        )

        embed_pipeline = IngestionPipeline(
            transformations=[self._embed_model],
            docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
            docstore=self._docstore,
            vector_store=self._vector_store,
        )

        docs = reader.load_data()
        logger.info(f'Read {len(docs)} documents')

        blocks_by_class_name: Any = {}
        blocks_by_function_name: Any = {}

        def index_callback(codeblock: CodeBlock):
            if codeblock.type == CodeBlockType.CLASS:
                if codeblock.identifier not in blocks_by_class_name:
                    blocks_by_class_name[codeblock.identifier] = []
                blocks_by_class_name[codeblock.identifier].append(
                    (codeblock.module.file_path, codeblock.full_path())
                )

            if codeblock.type == CodeBlockType.FUNCTION:
                if codeblock.identifier not in blocks_by_function_name:
                    blocks_by_function_name[codeblock.identifier] = []
                blocks_by_function_name[codeblock.identifier].append(
                    (codeblock.module.file_path, codeblock.full_path())
                )

        splitter = EpicSplitter(
            min_chunk_size=self._settings.min_chunk_size,
            chunk_size=self._settings.chunk_size,
            hard_token_limit=self._settings.hard_token_limit,
            max_chunks=self._settings.max_chunks,
            comment_strategy=self._settings.comment_strategy,
            index_callback=index_callback,
            repo_path=repo_path,
        )

        prepared_nodes = splitter.get_nodes_from_documents(docs, show_progress=True)
        prepared_tokens = sum(
            [
                count_tokens(node.get_content(), self._settings.embedding_model_name)
                for node in prepared_nodes
            ]
        )
        logger.info(
            f'Prepared {len(prepared_nodes)} nodes and {prepared_tokens} tokens'
        )

        embedded_nodes = embed_pipeline.run(
            nodes=list(prepared_nodes), show_progress=True, num_workers=num_workers
        )
        embedded_tokens = sum(
            [
                count_tokens(node.get_content(), self._settings.embedding_model_name)
                for node in embedded_nodes
            ]
        )
        logger.info(
            f'Embedded {len(embedded_nodes)} vectors with {embedded_tokens} tokens'
        )

        self._blocks_by_class_name = blocks_by_class_name
        self._blocks_by_function_name = blocks_by_function_name

        return len(embedded_nodes), embedded_tokens

    def persist(self, persist_dir: str):
        self._vector_store.persist(persist_dir)
        self._docstore.persist(
            os.path.join(persist_dir, docstore.types.DEFAULT_PERSIST_FNAME)
        )
        self._settings.persist(persist_dir)

        with open(os.path.join(persist_dir, 'blocks_by_class_name.json'), 'w') as f:
            f.write(json.dumps(self._blocks_by_class_name, indent=2))

        with open(os.path.join(persist_dir, 'blocks_by_function_name.json'), 'w') as f:
            f.write(json.dumps(self._blocks_by_function_name, indent=2))


def _rerank_files(file_paths: List[str], file_pattern: str):
    if len(file_paths) < 2:
        return file_paths

    tokenized_query = file_pattern.replace('.py', '').replace('*', '').split('/')
    tokenized_query = [part for part in tokenized_query if part.strip()]
    query = '/'.join(tokenized_query)

    scored_files = []
    for file_path in file_paths:
        cleaned_file_path = file_path.replace('.py', '')
        score = fuzz.partial_ratio(cleaned_file_path, query)
        scored_files.append((file_path, score))

    scored_files.sort(key=lambda x: x[1], reverse=True)

    sorted_file_paths = [file for file, score in scored_files]

    logger.info(
        f'rerank_files() Reranked {len(file_paths)} files with query {tokenized_query}. First hit {sorted_file_paths[0]}'
    )

    return sorted_file_paths
