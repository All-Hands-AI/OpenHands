import json
import os
from typing import Optional

from pydantic import BaseModel, Field


class IndexSettings(BaseModel):
    embedding_model_name: str = Field(
        default='text-embedding-3-small',
        description='The name of the embedding model to use',
    )
    embedding_model_provider: str = Field(
        default='openai', description='The provider of the embedding model'
    )
    embedding_dimensions: int = Field(
        default=1536, description='The number of dimensions in the embedding'
    )
    vector_engine: str = Field(default='faiss', description='The vector engine to use')
    existing_index_name: Optional[str] = Field(
        default=None, description='The name of an existing index to use'
    )

    def persist(self, persist_dir: str) -> None:
        with open(os.path.join(persist_dir, 'settings.json'), 'w') as f:
            json.dump(self.model_dump(), f)

    @classmethod
    def from_persist_dir(cls, persist_dir: str):
        with open(os.path.join(persist_dir, 'settings.json'), 'r') as f:
            data = json.load(f)
        return cls(**data)
