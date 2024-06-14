from enum import Enum

from llama_index.core.embeddings import BaseEmbedding


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
            # TODO: add more models like voyage, etc.

            pass
        case _:
            raise ValueError(f'Unknown embedding provider: {provider}')
