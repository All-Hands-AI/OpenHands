from llama_index.core.ingestion import IngestionPipeline
from llama_index.readers.gpt_repo import GPTRepoReader

from opendevin.indexing.rag.embedding import get_embedding_model
from opendevin.indexing.rag.repository import LocalRepository
from opendevin.indexing.rag.settings import IndexSettings
from opendevin.indexing.rag.storage import get_vector_store


class RAGIndex:
    def __init__(
        self,
        repo: LocalRepository,
        index_settings: IndexSettings,
    ) -> None:
        self._repo = repo
        self._index_settings = index_settings
        self._vector_store = get_vector_store(settings=index_settings)

        self._embedding_model = get_embedding_model(
            index_settings.embedding_model_provider, index_settings.embedding_model_name
        )

    def run_ingestion(self):
        repo_path = self._repo.path

        reader = GPTRepoReader()
        documents = reader.load_data(
            repo_path=repo_path, extensions=['.py', '.md', '.sh']
        )
        ingest_pipeline = IngestionPipeline(
            transformations=[
                self._embedding_model,
            ],
            vector_store=self._vector_store,
        )

        embedded_nodes = ingest_pipeline.run(documents=documents, show_progress=True)
        return embedded_nodes


if __name__ == '__main__':
    repo_path = './agenthub'
    index_settings = IndexSettings(
        vector_engine='pinecone',
        existing_index_name='test-code-index',
    )
    rag_index = RAGIndex(LocalRepository(repo_path), index_settings)

    nodes = rag_index.run_ingestion()

    print(f'Indexed {len(nodes)} nodes.')
