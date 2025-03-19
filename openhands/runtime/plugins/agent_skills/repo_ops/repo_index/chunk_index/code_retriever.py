import fnmatch
import mimetypes
import os
from typing import Dict

import Stemmer
from llama_index.core import SimpleDirectoryReader
from llama_index.retrievers.bm25 import BM25Retriever

from openhands.runtime.plugins.agent_skills.repo_ops.repo_index.chunk_index.index.epic_split import (
    EpicSplitter,
)


def build_code_retriever_from_repo(
    repo_path,
    similarity_top_k=10,
    min_chunk_size=100,
    chunk_size=500,
    max_chunk_size=2000,
    hard_token_limit=2000,
    max_chunks=200,
    persist_path=None,
    show_progress=False,
):
    # print(repo_path)
    # Only extract file name and type to not trigger unnecessary embedding jobs
    def file_metadata_func(file_path: str) -> Dict:
        # print(file_path)
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
        exclude=[
            '**/test/**',
            '**/tests/**',
            '**/test_*.py',
            '**/*_test.py',
        ],
        file_metadata=file_metadata_func,
        filename_as_id=True,
        required_exts=['.py'],  # TODO: Shouldn't be hardcoded and filtered
        recursive=True,
    )
    docs = reader.load_data()

    # splitter = CodeSplitter(
    #     language="python",
    #     chunk_lines=100,  # lines per chunk
    #     chunk_lines_overlap=15,  # lines overlap between chunks
    #     max_chars=3000,  # max chars per chunk
    # )

    splitter = EpicSplitter(
        min_chunk_size=min_chunk_size,
        chunk_size=chunk_size,
        max_chunk_size=max_chunk_size,
        hard_token_limit=hard_token_limit,
        max_chunks=max_chunks,
        repo_path=repo_path,
    )
    prepared_nodes = splitter.get_nodes_from_documents(
        docs, show_progress=show_progress
    )

    # We can pass in the index, docstore, or list of nodes to create the retriever
    retriever = BM25Retriever.from_defaults(
        nodes=prepared_nodes,
        similarity_top_k=similarity_top_k,
        stemmer=Stemmer.Stemmer('english'),
        language='english',
    )
    if persist_path:
        retriever.persist(persist_path)
    return retriever
    # keyword = 'FORBIDDEN_ALIAS_PATTERN'
    # retrieved_nodes = retriever.retrieve(keyword)
