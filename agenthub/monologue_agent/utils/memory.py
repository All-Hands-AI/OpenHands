import threading
from abc import ABC, abstractmethod

import chromadb
import llama_index.embeddings.openai.base as llama_openai
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.vector_stores.chroma import ChromaVectorStore
from openai._exceptions import APIConnectionError, InternalServerError, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from opendevin import config
from opendevin.logger import opendevin_logger as logger
from opendevin.schema.config import ConfigType

from . import json

num_retries = config.get(ConfigType.LLM_NUM_RETRIES)
retry_min_wait = config.get(ConfigType.LLM_RETRY_MIN_WAIT)
retry_max_wait = config.get(ConfigType.LLM_RETRY_MAX_WAIT)

# llama-index includes a retry decorator around openai.get_embeddings() function
# it is initialized with hard-coded values and errors
# this non-customizable behavior is creating issues when it's retrying faster than providers' rate limits
# this block attempts to banish it and replace it with our decorator, to allow users to set their own limits

if hasattr(llama_openai.get_embeddings, '__wrapped__'):
    original_get_embeddings = llama_openai.get_embeddings.__wrapped__
else:
    logger.warning('Cannot set custom retry limits.')  # warn
    num_retries = 1
    original_get_embeddings = llama_openai.get_embeddings


def attempt_on_error(retry_state):
    logger.error(f'{retry_state.outcome.exception()}. Attempt #{retry_state.attempt_number} | You can customize these settings in the configuration.', exc_info=False)
    return True


@retry(reraise=True,
       stop=stop_after_attempt(num_retries),
       wait=wait_random_exponential(min=retry_min_wait, max=retry_max_wait),
       retry=retry_if_exception_type((RateLimitError, APIConnectionError, InternalServerError)),
       after=attempt_on_error)
def wrapper_get_embeddings(*args, **kwargs):
    return original_get_embeddings(*args, **kwargs)


llama_openai.get_embeddings = wrapper_get_embeddings


class EmbeddingModelFactory(ABC):
    @abstractmethod
    def create_embedding_model(self, embedding_strategy: str | None):
        pass

    @classmethod
    def create(self, embedding_strategy: str | None):
        # TODO: More embeddings: https://docs.llamaindex.ai/en/stable/examples/embeddings/OpenAI/

        # If no embedding strategy is provided, use the one from the config
        # If that is also not provided, fall back to HuggingFace
        if embedding_strategy is None:
            embedding_strategy = config.get(ConfigType.LLM_EMBEDDING_MODEL)

        # Define a dict of factories for the embedding strategies we know
        factories = {
            'llama2': OllamaEmbeddingFactory(),
            'mxbai-embed-large': OllamaEmbeddingFactory(),
            'nomic-embed-text': OllamaEmbeddingFactory(),
            'all-minilm': OllamaEmbeddingFactory(),
            'stable-code': OllamaEmbeddingFactory(),
            'openai': OpenAIEmbeddingFactory(),
            'azureopenai': AzureOpenAIEmbeddingFactory(),
            'local': HuggingFaceEmbeddingFactory()
        }

        # Get the right factory for the embedding strategy
        factory = factories.get(embedding_strategy, HuggingFaceEmbeddingFactory())

        # Let the factory create the embedding model with whatever parameters it needs
        return factory.create_embedding_model(embedding_strategy)


class OllamaEmbeddingFactory(EmbeddingModelFactory):
    def create_embedding_model(self, embedding_strategy: str | None):
        from llama_index.embeddings.ollama import OllamaEmbedding
        return OllamaEmbedding(
            model_name=embedding_strategy,
            base_url=config.get(ConfigType.LLM_EMBEDDING_BASE_URL, required=True),
            ollama_additional_kwargs={'mirostat': 0},
        )

class OpenAIEmbeddingFactory(EmbeddingModelFactory):
    def create_embedding_model(self, embedding_strategy: str | None):
        from llama_index.embeddings.openai import OpenAIEmbedding
        embedding_strategy = 'text-embedding-ada-002'
        return OpenAIEmbedding(
            model= embedding_strategy,
            api_key=config.get(ConfigType.LLM_API_KEY, required=True)
        )

class AzureOpenAIEmbeddingFactory(EmbeddingModelFactory):
    def create_embedding_model(self, embedding_strategy: str | None):
        from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
        embedding_strategy = 'text-embedding-ada-002'
        return AzureOpenAIEmbedding(
            model= embedding_strategy,
            deployment_name=config.get(ConfigType.LLM_EMBEDDING_DEPLOYMENT_NAME, required=True),
            api_key=config.get(ConfigType.LLM_API_KEY, required=True),
            azure_endpoint=config.get(ConfigType.LLM_BASE_URL, required=True),
            api_version=config.get(ConfigType.LLM_API_VERSION, required=True),
        )

class HuggingFaceEmbeddingFactory(EmbeddingModelFactory):
    def create_embedding_model(self, embedding_strategy: str | None):
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        return HuggingFaceEmbedding(
            model_name='BAAI/bge-small-en-v1.5'
        )


class LongTermMemory:
    """
    Responsible for storing information that the agent can call on later for better insights and context.
    Uses chromadb to store and search through memories.
    """

    def __init__(self):
        """
        Initialize the chromadb and set up ChromaVectorStore for later use.
        """
        embedding_strategy = config.get(ConfigType.LLM_EMBEDDING_MODEL)
        embed_model = EmbeddingModelFactory.create(embedding_strategy=embedding_strategy)

        db = chromadb.Client()
        self.collection = db.get_or_create_collection(name='memories')
        vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.index = VectorStoreIndex.from_vector_store(
            vector_store, embed_model=embed_model)
        self.thought_idx = 0
        self._add_threads = []
        self.sema = threading.Semaphore(value=config.get(ConfigType.AGENT_MEMORY_MAX_THREADS))


    def add_event(self, event: dict):
        """
        Adds a new event to the long term memory with a unique id.

        Parameters:
        - event (dict): The new event to be added to memory
        """
        id = ''
        t = ''
        if 'action' in event:
            t = 'action'
            id = event['action']
        elif 'observation' in event:
            t = 'observation'
            id = event['observation']
        doc = Document(
            text=json.dumps(event),
            doc_id=str(self.thought_idx),
            extra_info={
                'type': t,
                'id': id,
                'idx': self.thought_idx,
            },
        )
        self.thought_idx += 1
        logger.debug('Adding %s event to memory: %d', t, self.thought_idx)
        thread = threading.Thread(target=self._add_doc, args=(doc,))
        self._add_threads.append(thread)
        thread.start()  # We add the doc concurrently so we don't have to wait ~500ms for the insert

    def _add_doc(self, doc):
        with self.sema:
            self.index.insert(doc)

    def search(self, query: str, k: int = 10):
        """
        Searches through the current memory using VectorIndexRetriever

        Parameters:
        - query (str): A query to match search results to
        - k (int): Number of top results to return

        Returns:
        - List[str]: List of top k results found in current memory
        """
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=k,
        )
        results = retriever.retrieve(query)
        return [r.get_text() for r in results]
