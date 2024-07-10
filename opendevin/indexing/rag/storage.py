import os
from enum import Enum
from typing import Optional

from llama_index.core.vector_stores.types import BasePydanticVectorStore

from opendevin.indexing.rag.settings import IndexSettings


class VectorEngine(Enum):
    CHROMADB = 'chromadb'

    PINECONE = 'pinecone'

    FAISS = 'faiss'


def get_vector_store(settings: IndexSettings) -> BasePydanticVectorStore:
    match VectorEngine(settings.vector_engine):
        case VectorEngine.PINECONE:
            return get_pinecone_vector_store(
                settings.embedding_dimensions, settings.existing_index_name
            )
        case VectorEngine.FAISS:
            return get_faiss_vector_store(
                settings.embedding_dimensions, settings.existing_index_name
            )
        case VectorEngine.CHROMADB:
            # TODO: add ChromaDBVectorStore
            pass
        case _:
            raise ValueError(f'Unknown vector engine: {settings.vector_engine}')


def get_pinecone_vector_store(
    embedding_dimensions: int, index_name: Optional[str] = None
) -> BasePydanticVectorStore:
    from llama_index.vector_stores.pinecone import PineconeVectorStore
    from pinecone import Pinecone, ServerlessSpec

    db = Pinecone(
        api_key=os.getenv('PINECONE_API_KEY'),
    )
    if index_name is None:
        index_name = 'mon-nouvel-indice'
        db.create_index(
            name=index_name,
            dimension=embedding_dimensions,
            spec=ServerlessSpec(cloud='aws', region='us-east-1'),
        )

    pc_index = db.Index(index_name)

    return PineconeVectorStore(pinecone_index=pc_index)


def get_faiss_vector_store(
    embedding_dimensions: int, index_name: Optional[str]
) -> BasePydanticVectorStore:
    import faiss
    from llama_index.vector_stores.faiss import FaissVectorStore

    faiss_index = faiss.IndexFlatL2(embedding_dimensions)
    return FaissVectorStore(faiss_index=faiss_index)
