import json
import os
from enum import Enum

from pydantic import BaseModel, Field


class CommentStrategy(Enum):
    # Keep comments
    INCLUDE = 'include'

    # Always associate comments before a code block with the code block
    ASSOCIATE = 'associate'

    # Exclude comments in parsed chunks
    EXCLUDE = 'exclude'


class IndexSettings(BaseModel):
    embed_model: str = Field(
        default='text-embedding-3-small', description='The embedding model to use.'
    )
    dimensions: int = Field(
        default=1536, description='The number of dimensions of the vectors.'
    )

    language: str = Field(default='python', description='The language of the code.')
    min_chunk_size: int = Field(default=100, description='The minimum chunk size.')
    chunk_size: int = Field(default=750, description='The soft max chunk size.')
    hard_token_limit: int = Field(default=2000, description='The hard token limit.')
    max_chunks: int = Field(
        default=200, description='The maximum number of chunks for one file.'
    )
    comment_strategy: CommentStrategy = Field(
        default=CommentStrategy.ASSOCIATE,
        description='Strategy on how comments will be indexed.',
    )

    def to_serializable_dict(self):
        data = self.dict()
        data['comment_strategy'] = data['comment_strategy'].value
        return data

    def persist(self, persist_dir: str):
        with open(os.path.join(persist_dir, 'settings.json'), 'w') as f:
            json.dump(self.to_serializable_dict(), f, indent=4)

    @classmethod
    def from_persist_dir(cls, persist_dir: str):
        with open(os.path.join(persist_dir, 'settings.json'), 'r') as f:
            data = json.load(f)
        return cls(**data)
