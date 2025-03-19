from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field


@dataclass
class CodeSnippet:
    id: str
    file_path: str
    content: Optional[str] = None
    distance: float = 0.0
    tokens: Optional[int] = None
    language: str = 'python'
    span_ids: Optional[List[str]] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    start_block: Optional[str] = None
    end_block: Optional[str] = None


class SpanHit(BaseModel):
    span_id: str = Field(description='The span id of the relevant code in the file')
    rank: int = Field(
        default=0,
        description='The rank of relevance of the span in the file. 0 is highest.',
    )
    tokens: int = Field(default=0, description='The number of tokens in the span.')


class SearchCodeHit(BaseModel):
    file_path: str = Field(
        description='The file path where the relevant code is found.'
    )
    spans: List[SpanHit] = Field(
        default_factory=list,
        description='The spans of the relevant code in the file',
    )

    @property
    def span_ids(self):
        return [span.span_id for span in self.spans]

    def add_span(self, span_id: str, rank: int = 0, tokens: int = 0):
        if span_id not in [span.span_id for span in self.spans]:
            self.spans.append(SpanHit(span_id=span_id, rank=rank, tokens=tokens))

    def contains_span(self, span_id: str) -> bool:
        return span_id in [span.span_id for span in self.spans]

    def add_spans(self, span_ids: List[str], rank: int = 0):
        for span_id in span_ids:
            self.add_span(span_id, rank)


class SearchCodeResponse(BaseModel):
    message: Optional[str] = Field(
        default=None, description='A message to return to the user.'
    )

    hits: List[SearchCodeHit] = Field(
        default_factory=list,
        description='Search results.',
    )
