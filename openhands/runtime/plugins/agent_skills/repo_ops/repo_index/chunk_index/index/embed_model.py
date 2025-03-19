import os

from llama_index.core.base.embeddings.base import BaseEmbedding


def get_embed_model(model_name: str) -> BaseEmbedding:
    if model_name.startswith('voyage'):
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
    else:
        # Assumes OpenAI otherwise
        try:
            from llama_index.embeddings.openai import OpenAIEmbedding
        except ImportError:
            raise ImportError(
                'llama-index-embeddings-openai is not installed. Please install it using `pip install llama-index-embeddings-openai`'
            )

        return OpenAIEmbedding(model_name=model_name)
