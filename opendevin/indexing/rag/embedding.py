import os
from enum import Enum

from dotenv import load_dotenv
from llama_index.core.embeddings import BaseEmbedding

load_dotenv()


class EmbeddingProvider(Enum):
    OPENAI = 'openai'

    HUGGINGFACE = 'huggingface'

    VOYAGE = 'voyage'


def get_embedding_model(provider: str, model_name: str) -> BaseEmbedding:
    match EmbeddingProvider(provider):
        case EmbeddingProvider.HUGGINGFACE:
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding

            return HuggingFaceEmbedding(
                model_name=model_name, embed_batch_size=3, trust_remote_code=True
            )
        case EmbeddingProvider.OPENAI:
            from llama_index.embeddings.openai import OpenAIEmbedding

            return OpenAIEmbedding(model_name=model_name)
        case EmbeddingProvider.VOYAGE:
            try:
                from llama_index.embeddings.voyageai import VoyageEmbedding
            except ImportError:
                raise ImportError(
                    'llama-index-embeddings-voyageai is not installed. Please install it using `pip install llama-index-embeddings-voyageai`'
                )

            if 'VOYAGE_API_KEY' not in os.environ:
                raise ValueError(
                    'VOYAGE_API_KEY environment variable is not set. Please set it to your Voyage API key.'
                )

            return VoyageEmbedding(
                model_name=model_name,
                voyage_api_key=os.environ.get('VOYAGE_API_KEY'),
                truncation=True,
                embed_batch_size=50,
            )
        case _:
            raise ValueError(f'Unknown embedding provider: {provider}')
