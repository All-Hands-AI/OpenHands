from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field


@dataclass
class RetrievedCodeSnippet:
    """
    A code snippet that has been retrieved from the index.
    """

    id: str
    file_path: str
    content: str
    start_line: Optional[int]
    end_line: Optional[int]
    similarity: float = 0.0
    language: str = 'python'
    span_ids: Optional[List[str]] = None


class FileSpanHit(BaseModel):
    span_id: str = Field(description='The unique identifier of the span in the file')

    rank: int = Field(
        default=0,
        description='The relevance rank of the span in the file. 0 is the highest rank.',
    )


class SearchCodeHit(BaseModel):
    """
    Each hit corresponds to a file that contains code snippets (spans) that match the query.
    """

    file_path: str = Field(
        description='The file path where the code snippet is located'
    )

    file_spans: List[FileSpanHit] = Field(
        default_factory=list, description='The spans in the file that match the query'
    )


class SearchCodeResponse(BaseModel):
    message: Optional[str] = Field(
        default=None, description='A message returned to the user'
    )

    hits: List[SearchCodeHit] = Field(
        default_factory=list, description='The code search results'
    )
