import importlib.util
import os

from joblib import Parallel, delayed

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger

try:
    # check if those we need later are available using importlib
    if importlib.util.find_spec('chromadb') is None:
        raise ImportError(
            'chromadb is not available. Please install it using poetry install --with llama-index'
        )

    if (
        importlib.util.find_spec(
            'llama_index.core.indices.vector_store.retrievers.retriever'
        )
        is None
        or importlib.util.find_spec('llama_index.core.indices.vector_store.base')
        is None
    ):
        raise ImportError(
            'llama_index is not available. Please install it using poetry install --with llama-index'
        )

    from llama_index.core import Document, VectorStoreIndex
    from llama_index.core.base.embeddings.base import BaseEmbedding
    from llama_index.core.ingestion import IngestionPipeline
    from llama_index.core.schema import TextNode

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


class EmbeddingsLoader:
    """Loader for embedding model initialization."""

    @staticmethod
    def get_embedding_model(strategy: str, llm_config: LLMConfig) -> 'BaseEmbedding':
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
        elif strategy == 'voyage':
            from llama_index.embeddings.voyageai import VoyageEmbedding

            return VoyageEmbedding(
                model_name='voyage-code-3',
            )
        elif (strategy is not None) and (strategy.lower() == 'none'):
            # TODO: this works but is not elegant enough. The incentive is when
            # an agent using embeddings is not used, there is no reason we need to
            # initialize an embedding model
            return None
        else:
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding

            # initialize the local embedding model
            local_embed_model = HuggingFaceEmbedding(
                model_name='BAAI/bge-small-en-v1.5'
            )

            # for local embeddings, we need torch
            import torch

            # choose the best device
            # first determine what is available: CUDA, MPS, or CPU
            if torch.cuda.is_available():
                device = 'cuda'
            elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
                device = 'mps'
            else:
                device = 'cpu'
                os.environ['CUDA_VISIBLE_DEVICES'] = ''
                os.environ['PYTORCH_FORCE_CPU'] = (
                    '1'  # try to force CPU to avoid errors
                )

                # override CUDA availability
                torch.cuda.is_available = lambda: False

            # disable MPS to avoid errors
            if device != 'mps' and hasattr(torch.backends, 'mps'):
                torch.backends.mps.is_available = lambda: False
                torch.backends.mps.is_built = False

            # the device being used
            logger.debug(f'Using device for embeddings: {device}')

            return local_embed_model


# --------------------------------------------------------------------------
# Utility functions to run pipelines, split out for profiling
# --------------------------------------------------------------------------
def run_pipeline(
    embed_model: 'BaseEmbedding', documents: list['Document'], num_workers: int
) -> list['TextNode']:
    """Run a pipeline embedding documents."""

    # set up a pipeline with the transformations to make
    pipeline = IngestionPipeline(
        transformations=[
            embed_model,
        ],
    )

    # run the pipeline with num_workers
    nodes = pipeline.run(
        documents=documents, show_progress=True, num_workers=num_workers
    )
    return nodes


def insert_batch_docs(
    index: 'VectorStoreIndex', documents: list['Document'], num_workers: int
) -> list['TextNode']:
    """Run the document indexing in parallel."""
    results = Parallel(n_jobs=num_workers, backend='threading')(
        delayed(index.insert)(doc) for doc in documents
    )
    return results
