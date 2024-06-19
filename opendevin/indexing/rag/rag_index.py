from typing import Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import CodeSplitter, NodeParser
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.vector_stores.types import (
    FilterCondition,
    MetadataFilter,
    MetadataFilters,
    VectorStoreQuery,
)

from .embedding import get_embedding_model
from .settings import IndexSettings
from .storage import get_vector_store


class RAGIndex:
    def __init__(
        self,
        index_settings: IndexSettings,
        splitter: Optional[NodeParser] = None,
    ) -> None:
        self._index_settings = index_settings
        self._splitter = (
            splitter
            if splitter is not None
            else CodeSplitter(language='python', max_chars=15000)
        )
        self._vector_store = get_vector_store(settings=index_settings)

        self._embedding_model = get_embedding_model(
            index_settings.embedding_model_provider, index_settings.embedding_model_name
        )
        self._index = VectorStoreIndex.from_vector_store(
            vector_store=self._vector_store,
            embed_model=self._embedding_model,
        )

    def run_ingestion(self, repo_path: str):
        reader = SimpleDirectoryReader(
            input_dir=repo_path,
            # file_metadata=file_metadata_func,
            # input_files=input_files,
            filename_as_id=True,
            required_exts=['.py'],  # TODO: Shouldn't be hardcoded and filtered
            recursive=True,
        )
        documents = reader.load_data(show_progress=True)
        print(f'Loaded {len(documents)} documents.')
        ingest_pipeline = IngestionPipeline(
            transformations=[
                self._splitter,
                self._embedding_model,
            ],
            vector_store=self._vector_store,
        )

        embedded_nodes = ingest_pipeline.run(documents=documents, show_progress=True)
        return embedded_nodes

    def semantic_search(self, query: Optional[str] = None, top_k: int = 5):
        # retriever = VectorIndexRetriever(
        #     index=self._index,
        #     similarity_top_k=top_k,
        # )
        # results = retriever.retrieve(query)
        # return [(r.get_text(), r.node.metadata) for r in results]

        # TODO:
        search_results = self._vector_search(query or '')
        print(search_results)
        raise NotImplementedError()

    def _vector_search(
        self,
        query: str,
        category: str = 'implementation',
    ):
        query_embedding = self._embedding_model.get_query_embedding(query)
        filters = MetadataFilters(filters=[], condition=FilterCondition.AND)
        if category:
            filters.filters.append(MetadataFilter(key='category', value=category))
        query_bundle = VectorStoreQuery(
            query_str=query,
            query_embedding=query_embedding,
            similarity_top_k=100,  # FIXME: Hardcoded
            filters=filters,
        )

        result = self._vector_store.query(query=query_bundle)
        for node_id, sim_score in zip(result.ids, result.similarities):
            # TODO: convert to `RetrievedCodeSnippet`
            continue

        raise NotImplementedError()


if __name__ == '__main__':
    repo_path = '/Users/ryan/Developer/OpenDevin'
    index_settings = IndexSettings(
        vector_engine='pinecone',
        # existing_index_name='test-code-index',
    )
    # rag_index = RAGIndex(LocalRepository(repo_path), index_settings)

    # nodes = rag_index.run_ingestion()
    # print(f'Indexed {len(nodes)} nodes.')

    # search_results = rag_index.semantic_search(
    #     query='viewcode creates pages for epub even if `viewcode_enable_epub=False` on `make html epub`',
    #     top_k=3,
    # )

    # for i, r in enumerate(search_results):
    #     text, metadata = r
    #     for key, value in metadata.items():
    #         print(key + ': ' + str(value))
    #     print(f'Text: {text}')
