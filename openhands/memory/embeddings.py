from openhands.core.config import LLMConfig

try:
    import chromadb
    from llama_index.core import Document, VectorStoreIndex
    from llama_index.core.retrievers import VectorIndexRetriever
    from llama_index.vector_stores.chroma import ChromaVectorStore

    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False

# Define supported embedding models
SUPPORTED_OLLAMA_EMBED_MODELS = [
    'llama2',
    'mxbai-embed-large',
    'nomic-embed-text',
    'all-minilm',
    'stable-code',
    'bge-m3',
    'bge-large',
    'paraphrase-multilingual',
    'snowflake-arctic-embed',
]


def check_llama_index():
    """Utility function to check the availability of llama_index.

    Raises:
        ImportError: If llama_index is not available.
    """
    if not LLAMA_INDEX_AVAILABLE:
        raise ImportError(
            'llama_index and its dependencies are not installed. '
            'To use memory features, please run: poetry install --with llama-index.'
        )
    return LLAMA_INDEX_AVAILABLE


check_llama_index()


class EmbeddingsLoader:
    """Loader for embedding model initialization."""

    @staticmethod
    def get_embedding_model(strategy: str, llm_config: LLMConfig):
        """Initialize and return the appropriate embedding model based on the strategy.

        Parameters:
        - strategy: The embedding strategy to use.
        - llm_config: Configuration for the LLM.

        Returns:
        - An instance of the selected embedding model or None.
        """

        if strategy in SUPPORTED_OLLAMA_EMBED_MODELS:
            from llama_index.embeddings.ollama import OllamaEmbedding

            return OllamaEmbedding(
                model_name=strategy,
                base_url=llm_config.embedding_base_url,
                ollama_additional_kwargs={'mirostat': 0},
            )
        elif strategy == 'openai':
            from llama_index.embeddings.openai import OpenAIEmbedding

            return OpenAIEmbedding(
                model='text-embedding-ada-002',
                api_key=llm_config.api_key,
            )
        elif strategy == 'azureopenai':
            from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

            return AzureOpenAIEmbedding(
                model='text-embedding-ada-002',
                deployment_name=llm_config.embedding_deployment_name,
                api_key=llm_config.api_key,
                azure_endpoint=llm_config.base_url,
                api_version=llm_config.api_version,
            )
        elif (strategy is not None) and (strategy.lower() == 'none'):
            # TODO: this works but is not elegant enough. The incentive is when
            # an agent using embeddings is not used, there is no reason we need to
            # initialize an embedding model
            return None
        else:
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding

            return HuggingFaceEmbedding(model_name='BAAI/bge-small-en-v1.5')
