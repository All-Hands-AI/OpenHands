# import fnmatch
# import json
# import logging
# import mimetypes
# import os
# import shutil
# import tempfile
# from typing import Dict, List, Optional

# import requests
# from llama_index.core import SimpleDirectoryReader
# from llama_index.core.base.embeddings.base import BaseEmbedding
# from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
# from llama_index.core.storage import docstore
# from llama_index.core.storage.docstore import DocumentStore, SimpleDocumentStore
# from llama_index.core.vector_stores.types import (
#     BasePydanticVectorStore,
#     FilterCondition,
#     MetadataFilter,
#     MetadataFilters,
#     VectorStoreQuery,
# )
# from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

# from rapidfuzz import fuzz

# from ..codeblocks.codeblocks import (
#     CodeBlock,
#     CodeBlockType,
# )
# from .embed_model import get_embed_model
# from .epic_split import EpicSplitter
# from .settings import IndexSettings
# from .simple_faiss import SimpleFaissVectorStore
# from .types import (
#     CodeSnippet,
#     SearchCodeHit,
#     SearchCodeResponse,
# )
# from ..repository import (
#     FileRepository,
# )
# from ..types import (
#     FileWithSpans,
# )
# from ..utils.tokenizer import (
#     count_tokens,
# )

# logger = logging.getLogger(__name__)


# def default_vector_store(settings: IndexSettings):
#     try:
#         import faiss
#     except ImportError:
#         raise ImportError(
#             "faiss needs to be installed to set up a default index for CodeIndex. Run 'pip install faiss-cpu'"
#         )

#     faiss_index = faiss.IndexIDMap(faiss.IndexFlatL2(settings.dimensions))
#     return SimpleFaissVectorStore(faiss_index)


# class CodeIndex:
#     def __init__(
#         self,
#         file_repo: FileRepository,
#         vector_store: Optional[BasePydanticVectorStore] = None,
#         docstore: Optional[DocumentStore] = None,
#         embed_model: Optional[BaseEmbedding] = None,
#         blocks_by_class_name: Optional[dict] = None,
#         blocks_by_function_name: Optional[dict] = None,
#         settings: Optional[IndexSettings] = None,
#         max_results: int = 25,
#         max_hits_without_exact_match: int = 100,
#         max_exact_results: int = 5,
#     ):
#         self._settings = settings or IndexSettings()

#         self.max_results = max_results
#         self.max_hits_without_exact_match = max_hits_without_exact_match
#         self.max_exact_results = max_exact_results

#         self._file_repo = file_repo

#         self._blocks_by_class_name = blocks_by_class_name or {}
#         self._blocks_by_function_name = blocks_by_function_name or {}

#         self._embed_model = embed_model or get_embed_model(self._settings.embed_model)
#         self._vector_store = vector_store or default_vector_store(self._settings)
#         self._docstore = docstore or SimpleDocumentStore()

#     @classmethod
#     def from_persist_dir(cls, persist_dir: str, file_repo: FileRepository, **kwargs):
#         vector_store = SimpleFaissVectorStore.from_persist_dir(persist_dir)
#         docstore = SimpleDocumentStore.from_persist_dir(persist_dir)

#         settings = IndexSettings.from_persist_dir(persist_dir)
#         embed_model = AzureOpenAIEmbedding(
#             model='text-embedding-3-small',
#             deployment_name='miblab-text-embed-small',
#             api_key=os.environ.get('AZURE_OPENAI_API_KEY_EMBED'),
#             azure_endpoint=os.environ.get('AZURE_OPENAI_ENDPOINT_EMBED'),
#             api_version='2024-06-01',
#         )

#         if os.path.exists(os.path.join(persist_dir, 'blocks_by_class_name.json')):
#             with open(os.path.join(persist_dir, 'blocks_by_class_name.json'), 'r') as f:
#                 blocks_by_class_name = json.load(f)
#         else:
#             blocks_by_class_name = {}

#         if os.path.exists(os.path.join(persist_dir, 'blocks_by_function_name.json')):
#             with open(
#                 os.path.join(persist_dir, 'blocks_by_function_name.json'), 'r'
#             ) as f:
#                 blocks_by_function_name = json.load(f)
#         else:
#             blocks_by_function_name = {}

#         return cls(
#             file_repo=file_repo,
#             vector_store=vector_store,
#             docstore=docstore,
#             embed_model=embed_model,
#             settings=settings,
#             blocks_by_class_name=blocks_by_class_name,
#             blocks_by_function_name=blocks_by_function_name,
#             **kwargs,
#         )

#     @classmethod
#     def from_url(cls, url: str, persist_dir: str, file_repo: FileRepository):
#         try:
#             response = requests.get(url, stream=True)
#             response.raise_for_status()

#             with tempfile.TemporaryDirectory() as temp_dir:
#                 temp_zip_file = os.path.join(temp_dir, url.split('/')[-1])

#                 with open(temp_zip_file, 'wb') as data:
#                     for chunk in response.iter_content(chunk_size=8192):
#                         data.write(chunk)

#                 shutil.unpack_archive(temp_zip_file, persist_dir)

#         except requests.exceptions.HTTPError as e:
#             logger.exception(f'HTTP Error while fetching {url}')
#             raise e
#         except Exception as e:
#             logger.exception(f'Failed to download {url}')
#             raise e

#         logger.info(f'Downloaded existing index from {url}.')

#         vector_store = SimpleFaissVectorStore.from_persist_dir(persist_dir)
#         docstore = SimpleDocumentStore.from_persist_dir(persist_dir)

#         if not os.path.exists(os.path.join(persist_dir, 'settings.json')):
#             # TODO: Remove this when new indexes are uploaded
#             settings = IndexSettings(embed_model='voyage-code-2')
#         else:
#             settings = IndexSettings.from_persist_dir(persist_dir)

#         return cls(
#             file_repo=file_repo,
#             vector_store=vector_store,
#             docstore=docstore,
#             settings=settings,
#         )

#     def search(
#         self,
#         query: Optional[str] = None,
#         code_snippet: Optional[str] = None,
#         class_names: Optional[List[str]] = None,
#         function_names: Optional[List[str]] = None,
#         file_pattern: Optional[str] = None,
#         max_results: int = 25,
#     ) -> SearchCodeResponse:
#         if class_names or function_names:
#             result = self.find_by_name(
#                 class_names=class_names,
#                 function_names=function_names,
#                 file_pattern=file_pattern,
#             )

#             if len(result.hits) == 0 and class_names and function_names:
#                 results = []
#                 results.extend(
#                     self.find_by_name(
#                         class_names=class_names,
#                         file_pattern=file_pattern,
#                         include_functions_in_class=False,
#                     ).hits
#                 )
#                 results.extend(
#                     self.find_by_name(
#                         function_names=function_names, file_pattern=file_pattern
#                     ).hits
#                 )

#                 if len(results) > 0 and len(results) <= max_results:
#                     return SearchCodeResponse(
#                         message=f'Found {len(results)} hits.',
#                         hits=results,
#                     )

#         if query or code_snippet:
#             return self.semantic_search(
#                 query=query,
#                 code_snippet=code_snippet,
#                 class_names=class_names,
#                 function_names=function_names,
#                 file_pattern=file_pattern,
#                 max_results=max_results,
#             )

#         return result

#     def semantic_search(
#         self,
#         query: Optional[str] = None,
#         code_snippet: Optional[str] = None,
#         class_names: Optional[List[str]] = None,
#         function_names: Optional[List[str]] = None,
#         file_pattern: Optional[str] = None,
#         category: str = 'implementation',
#         max_results: int = 25,
#         max_hits_without_exact_match: int = 100,
#         max_exact_results: int = 5,
#         max_spans_per_file: Optional[int] = None,
#         exact_match_if_possible: bool = False,
#     ) -> SearchCodeResponse:
#         if query is None:
#             query = ''

#         if class_names:
#             query += f', class {class_names}'

#         if function_names:
#             query += f', function {function_names}'

#         message = ''
#         if file_pattern:
#             if category != 'test':
#                 exclude_files = self._file_repo.matching_files('**/test*/**')
#             else:
#                 exclude_files = []

#             matching_files = self._file_repo.matching_files(file_pattern)
#             matching_files = [
#                 file for file in matching_files if file not in exclude_files
#             ]

#             if not matching_files:
#                 logger.info(
#                     f'semantic_search() No files found for file pattern {file_pattern}. Will search all files...'
#                 )
#                 message += f'No files found for file pattern {file_pattern}. Will search all files.\n'
#                 file_pattern = None

#         search_results = self._vector_search(
#             query, file_pattern=file_pattern, exact_content_match=code_snippet
#         )

#         files_with_spans: dict[str, SearchCodeHit] = {}

#         span_count = 0
#         spans_with_exact_query_match = 0
#         filtered_out = 0

#         require_exact_query_match = False

#         for rank, search_hit in enumerate(search_results):
#             file = self._file_repo.get_file(search_hit.file_path)
#             if not file:
#                 logger.warning(
#                     f'semantic_search() Could not find file {search_hit.file_path}.'
#                 )
#                 continue

#             spans = []
#             for span_id in search_hit.span_ids:
#                 span = file.module.find_span_by_id(span_id)

#                 if span:
#                     spans.append(span)
#                 else:
#                     logger.debug(
#                         f'semantic_search() Could not find span with id {span_id} in file {file.file_path}'
#                     )

#                     spans_by_line_number = file.module.find_spans_by_line_numbers(
#                         search_hit.start_line, search_hit.end_line
#                     )

#                     for span_by_line_number in spans_by_line_number:
#                         spans.append(span_by_line_number)

#             names = []
#             if class_names:
#                 names.extend(class_names)

#             if function_names:
#                 names.extend(function_names)

#             for span in spans:
#                 has_exact_query_match = (
#                     exact_match_if_possible
#                     and query
#                     and span.initiating_block.has_content(query, span.span_id)
#                 )

#                 if has_exact_query_match:
#                     spans_with_exact_query_match += 1

#                 if has_exact_query_match and not require_exact_query_match:
#                     require_exact_query_match = True
#                     files_with_spans = {}

#                 if (
#                     not require_exact_query_match and span_count <= max_results
#                 ) or has_exact_query_match:
#                     if search_hit.file_path not in files_with_spans:
#                         files_with_spans[search_hit.file_path] = SearchCodeHit(
#                             file_path=search_hit.file_path
#                         )

#                     if files_with_spans[search_hit.file_path].contains_span(
#                         span.span_id
#                     ):
#                         continue

#                     if names and not any(
#                         name in span.initiating_block.full_path() for name in names
#                     ):
#                         filtered_out += 1
#                         continue

#                     span_count += 1
#                     files_with_spans[search_hit.file_path].add_span(
#                         span_id=span.span_id, rank=rank, tokens=span.tokens
#                     )

#                     if (
#                         max_spans_per_file
#                         and len(files_with_spans[search_hit.file_path].spans)
#                         >= max_spans_per_file
#                     ):
#                         break

#             if exact_match_if_possible:
#                 if spans_with_exact_query_match > max_exact_results or (
#                     spans_with_exact_query_match == 0
#                     and span_count > max_hits_without_exact_match
#                 ):
#                     break
#             elif span_count > max_results:
#                 break

#         span_count = sum([len(file.spans) for file in files_with_spans.values()])

#         if class_names or function_names:
#             logger.info(
#                 f'semantic_search() Filtered out {filtered_out} spans by class names {class_names} and function names {function_names}.'
#             )

#         if require_exact_query_match:
#             logger.info(
#                 f'semantic_search() Found {spans_with_exact_query_match} code spans with exact match out of {span_count} spans.'
#             )
#             message = f'Found {spans_with_exact_query_match} code spans with code that matches the exact query `{query}`.'
#         else:
#             logger.info(
#                 f'semantic_search() Found {span_count} code spans in {len(files_with_spans.values())} files.'
#             )
#             message = f'Found {span_count} code spans.'

#         return SearchCodeResponse(message=message, hits=list(files_with_spans.values()))

#     def find_by_name(
#         self,
#         class_names: Optional[List[str]] = None,
#         function_names: Optional[List[str]] = None,
#         file_pattern: Optional[str] = None,
#         include_functions_in_class: bool = True,
#         category: str = 'implementation',
#     ) -> SearchCodeResponse:
#         if not class_names and not function_names:
#             raise ValueError(
#                 'At least one of class_name or function_name must be provided.'
#             )

#         paths = []

#         if function_names:
#             for function_name in function_names:
#                 paths.extend(self._blocks_by_function_name.get(function_name, []))

#         if class_names:
#             for class_name in class_names:
#                 paths.extend(self._blocks_by_class_name.get(class_name, []))

#         logger.info(
#             f'find_by_name(class_name={class_names}, function_name={function_names}, file_pattern={file_pattern}) {len(paths)} hits.'
#         )

#         if not paths:
#             if function_names:
#                 return SearchCodeResponse(
#                     message=f'No functions found with the name {function_names}.'
#                 )
#             else:
#                 return SearchCodeResponse(
#                     message=f'No classes found with the name {class_names}.'
#                 )

#         if category != 'test':
#             exclude_files = self._file_repo.matching_files('**/test*/**')

#             filtered_paths = []
#             for file_path, block_path in paths:
#                 if file_path not in exclude_files:
#                     filtered_paths.append((file_path, block_path))

#             filtered_out_test_files = len(paths) - len(filtered_paths)
#             if filtered_out_test_files > 0:
#                 logger.info(
#                     f'find_by_name() Filtered out {filtered_out_test_files} test files.'
#                 )

#             paths = filtered_paths

#         check_all_files = False
#         if file_pattern:
#             include_files = self._file_repo.matching_files(file_pattern)

#             if include_files:
#                 filtered_paths = []
#                 for file_path, block_path in paths:
#                     if file_path in include_files:
#                         filtered_paths.append((file_path, block_path))

#                 filtered_out_by_file_pattern = len(paths) - len(filtered_paths)
#                 if filtered_paths:
#                     logger.info(
#                         f'find_by_name() Filtered out {filtered_out_by_file_pattern} files by file pattern.'
#                     )
#                     paths = filtered_paths
#                 else:
#                     logger.info(
#                         f'find_by_name() No files found for file pattern {file_pattern}. Will search all files...'
#                     )
#                     check_all_files = True

#         filtered_out_by_class_name = 0
#         invalid_blocks = 0

#         files_with_spans = {}
#         for file_path, block_path in paths:
#             file = self._file_repo.get_file(file_path)
#             block = file.module.find_by_path(block_path)

#             if not block:
#                 invalid_blocks += 1
#                 continue

#             if (
#                 class_names
#                 and function_names
#                 and not self._found_class(block, class_names)
#             ):
#                 filtered_out_by_class_name += 1
#                 continue

#             if file_path not in files_with_spans:
#                 files_with_spans[file_path] = SearchCodeHit(file_path=file_path)

#             files_with_spans[file_path].add_span(
#                 block.belongs_to_span.span_id,
#                 rank=0,
#                 tokens=block.belongs_to_span.tokens,
#             )
#             if include_functions_in_class and not function_names:
#                 for child in block.children:
#                     if (
#                         child.belongs_to_span.span_id
#                         not in files_with_spans[file_path].span_ids
#                     ):
#                         files_with_spans[file_path].add_span(
#                             child.belongs_to_span.span_id,
#                             rank=0,
#                             tokens=child.belongs_to_span.tokens,
#                         )

#         if filtered_out_by_class_name > 0:
#             logger.info(
#                 f'find_by_function_name() Filtered out {filtered_out_by_class_name} functions by class name {class_name}.'
#             )

#         if invalid_blocks > 0:
#             logger.info(
#                 f'find_by_function_name() Ignored {invalid_blocks} invalid blocks.'
#             )

#         if check_all_files and len(files_with_spans) > 0:
#             message = f"The file pattern {file_pattern} didn't match any files. But I found {len(files_with_spans)} matches in other files."
#         elif len(files_with_spans):
#             message = f'Found {len(files_with_spans)} hits.'
#         elif class_names and function_names:
#             message = f'No functions found with the names {function_names} in class {class_names}.'
#         elif class_names:
#             message = f'No classes found with the name {class_names}.'
#         elif function_names:
#             message = f'No functions found with the names {function_names}.'
#         else:
#             message = 'No results found.'

#         file_paths = [file.file_path for file in files_with_spans.values()]
#         if file_pattern:
#             file_paths = _rerank_files(file_paths, file_pattern)

#         search_hits = []
#         for rank, file_path in enumerate(file_paths):
#             file = files_with_spans[file_path]
#             for span in file.spans:
#                 span.rank = rank
#             search_hits.append(file)

#         return SearchCodeResponse(
#             message=message,
#             hits=search_hits,
#         )

#     def _found_class(self, block: CodeBlock, class_names: list[str]):
#         for class_name in class_names:
#             parent_class = block.find_type_in_parents(CodeBlockType.CLASS)
#             if parent_class and parent_class.identifier == class_name:
#                 return True
#         else:
#             return False

#     def _create_search_hit(self, file: FileWithSpans, rank: int = 0):
#         file_hit = SearchCodeHit(file_path=file.file_path)
#         for span_id in file.span_ids:
#             file_hit.add_span(span_id, rank)
#         return file_hit

#     def _vector_search(
#         self,
#         query: str = '',
#         exact_query_match: bool = False,
#         category: str = 'implementation',
#         file_pattern: Optional[str] = None,
#         exact_content_match: Optional[str] = None,
#     ):
#         if file_pattern:
#             query += f' file:{file_pattern}'

#         if exact_content_match:
#             query += '\n' + exact_content_match

#         if not query:
#             raise ValueError(
#                 'At least one of query, span_keywords or content_keywords must be provided.'
#             )

#         logger.info(
#             f'vector_search() Searching for query [{query[:50]}...] and file pattern [{file_pattern}].'
#         )

#         query_embedding = self._embed_model.get_query_embedding(query)

#         filters = MetadataFilters(filters=[], condition=FilterCondition.AND)
#         if category:
#             filters.filters.append(MetadataFilter(key='category', value=category))

#         query_bundle = VectorStoreQuery(
#             query_str=query,
#             query_embedding=query_embedding,
#             similarity_top_k=500,  # TODO: Fix paging?
#             filters=filters,
#         )

#         result = self._vector_store.query(query_bundle)

#         filtered_out_snippets = 0
#         ignored_removed_snippets = 0
#         sum_tokens = 0

#         sum_tokens_per_file = {}

#         if file_pattern:
#             include_files = self._file_repo.matching_files(file_pattern)
#             if len(include_files) == 0:
#                 logger.info(
#                     f'vector_search() No files found for file pattern {file_pattern}, return empty result...'
#                 )
#                 return []
#         else:
#             include_files = []

#         if category != 'test':
#             exclude_files = self._file_repo.find_files(
#                 ['**/tests/**', 'tests*', '*_test.py', 'test_*.py']
#             )
#         else:
#             exclude_files = set()

#         search_results = []

#         for node_id, distance in zip(result.ids, result.similarities):
#             node_doc = self._docstore.get_document(node_id, raise_error=False)
#             if not node_doc:
#                 ignored_removed_snippets += 1
#                 # TODO: Retry to get top_k results
#                 continue

#             if exclude_files and node_doc.metadata['file_path'] in exclude_files:
#                 filtered_out_snippets += 1
#                 continue

#             if include_files and node_doc.metadata['file_path'] not in include_files:
#                 filtered_out_snippets += 1
#                 continue

#             if exact_query_match and query not in node_doc.get_content():
#                 filtered_out_snippets += 1
#                 continue

#             if exact_content_match:
#                 if not is_string_in(exact_content_match, node_doc.get_content()):
#                     filtered_out_snippets += 1
#                     continue

#             if node_doc.metadata['file_path'] not in sum_tokens_per_file:
#                 sum_tokens_per_file[node_doc.metadata['file_path']] = 0

#             sum_tokens += node_doc.metadata['tokens']
#             sum_tokens_per_file[node_doc.metadata['file_path']] += node_doc.metadata[
#                 'tokens'
#             ]

#             code_snippet = CodeSnippet(
#                 id=node_doc.id_,
#                 file_path=node_doc.metadata['file_path'],
#                 distance=distance,
#                 content=node_doc.get_content(),
#                 tokens=node_doc.metadata['tokens'],
#                 span_ids=node_doc.metadata.get('span_ids', []),
#                 start_line=node_doc.metadata.get('start_line', None),
#                 end_line=node_doc.metadata.get('end_line', None),
#             )

#             search_results.append(code_snippet)

#         # TODO: Rerank by file pattern if no exact matches on file pattern

#         logger.info(
#             f'vector_search() Returning {len(search_results)} search results. '
#             f'(Ignored {ignored_removed_snippets} removed search results. '
#             f'Filtered out {filtered_out_snippets} search results.)'
#         )

#         return search_results

#     def run_ingestion(
#         self,
#         repo_path: Optional[str] = None,
#         input_files: Optional[list[str]] = None,
#         num_workers: Optional[int] = None,
#     ):
#         repo_path = repo_path or self._file_repo.path

#         # Only extract file name and type to not trigger unnecessary embedding jobs
#         def file_metadata_func(file_path: str) -> Dict:
#             file_path = file_path.replace(repo_path, '')
#             if file_path.startswith('/'):
#                 file_path = file_path[1:]

#             test_patterns = [
#                 '**/test/**',
#                 '**/tests/**',
#                 '**/test_*.py',
#                 '**/*_test.py',
#             ]
#             category = (
#                 'test'
#                 if any(fnmatch.fnmatch(file_path, pattern) for pattern in test_patterns)
#                 else 'implementation'
#             )

#             return {
#                 'file_path': file_path,
#                 'file_name': os.path.basename(file_path),
#                 'file_type': mimetypes.guess_type(file_path)[0],
#                 'category': category,
#             }

#         reader = SimpleDirectoryReader(
#             input_dir=repo_path,
#             file_metadata=file_metadata_func,
#             input_files=input_files,
#             filename_as_id=True,
#             required_exts=['.py'],  # TODO: Shouldn't be hardcoded and filtered
#             recursive=True,
#         )

#         embed_pipeline = IngestionPipeline(
#             transformations=[self._embed_model],
#             docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
#             docstore=self._docstore,
#             vector_store=self._vector_store,
#         )

#         docs = reader.load_data()
#         logger.info(f'Read {len(docs)} documents')

#         blocks_by_class_name: dict[str, list] = {}
#         blocks_by_function_name: dict[str, list] = {}

#         def index_callback(codeblock: CodeBlock):
#             if codeblock.identifier is None:
#                 return

#             if codeblock.type == CodeBlockType.CLASS:
#                 if codeblock.identifier not in blocks_by_class_name:
#                     blocks_by_class_name[codeblock.identifier] = []
#                 blocks_by_class_name[codeblock.identifier].append(
#                     (codeblock.module.file_path, codeblock.full_path())
#                 )

#             if codeblock.type == CodeBlockType.FUNCTION:
#                 if codeblock.identifier not in blocks_by_function_name:
#                     blocks_by_function_name[codeblock.identifier] = []
#                 blocks_by_function_name[codeblock.identifier].append(
#                     (codeblock.module.file_path, codeblock.full_path())
#                 )

#         splitter = EpicSplitter(
#             min_chunk_size=self._settings.min_chunk_size,
#             chunk_size=self._settings.chunk_size,
#             hard_token_limit=self._settings.hard_token_limit,
#             max_chunks=self._settings.max_chunks,
#             comment_strategy=self._settings.comment_strategy,
#             index_callback=index_callback,
#             repo_path=repo_path,
#         )

#         prepared_nodes = splitter.get_nodes_from_documents(docs, show_progress=True)
#         prepared_tokens = sum(
#             [
#                 count_tokens(node.get_content(), self._settings.embed_model)
#                 for node in prepared_nodes
#             ]
#         )
#         logger.info(
#             f'Prepared {len(prepared_nodes)} nodes and {prepared_tokens} tokens'
#         )

#         embedded_nodes = embed_pipeline.run(
#             nodes=list(prepared_nodes), show_progress=True, num_workers=num_workers
#         )
#         embedded_tokens = sum(
#             [
#                 count_tokens(node.get_content(), self._settings.embed_model)
#                 for node in embedded_nodes
#             ]
#         )
#         logger.info(
#             f'Embedded {len(embedded_nodes)} vectors with {embedded_tokens} tokens'
#         )

#         self._blocks_by_class_name = blocks_by_class_name
#         self._blocks_by_function_name = blocks_by_function_name

#         return len(embedded_nodes), embedded_tokens

#     def persist(self, persist_dir: str):
#         self._vector_store.persist(persist_dir)
#         self._docstore.persist(
#             os.path.join(persist_dir, docstore.types.DEFAULT_PERSIST_FNAME)
#         )
#         self._settings.persist(persist_dir)

#         with open(os.path.join(persist_dir, 'blocks_by_class_name.json'), 'w') as f:
#             f.write(json.dumps(self._blocks_by_class_name, indent=2))

#         with open(os.path.join(persist_dir, 'blocks_by_function_name.json'), 'w') as f:
#             f.write(json.dumps(self._blocks_by_function_name, indent=2))


# def _rerank_files(file_paths: List[str], file_pattern: str):
#     if len(file_paths) < 2:
#         return file_paths

#     tokenized_query = file_pattern.replace('.py', '').replace('*', '').split('/')
#     tokenized_query = [part for part in tokenized_query if part.strip()]
#     query = '/'.join(tokenized_query)

#     scored_files = []
#     for file_path in file_paths:
#         cleaned_file_path = file_path.replace('.py', '')
#         score = fuzz.partial_ratio(cleaned_file_path, query)
#         scored_files.append((file_path, score))

#     scored_files.sort(key=lambda x: x[1], reverse=True)

#     sorted_file_paths = [file for file, score in scored_files]

#     logger.info(
#         f'rerank_files() Reranked {len(file_paths)} files with query {tokenized_query}. First hit {sorted_file_paths[0]}'
#     )

#     return sorted_file_paths


# def is_string_in(s1, s2):
#     s1_clean = s1.replace(' ', '').replace('\t', '').replace('\n', '')
#     s2_clean = s2.replace(' ', '').replace('\t', '').replace('\n', '')
#     found_in = s1_clean in s2_clean
#     return found_in
