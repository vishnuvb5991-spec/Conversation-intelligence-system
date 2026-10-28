from datetime import datetime
from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str
    source: str
    title: str
    text: str
    author: str | None = None
    url: str | None = None
    created_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class Chunk(BaseModel):
    id: str
    document_id: str
    source: str
    title: str
    text: str
    author: str | None = None
    url: str | None = None
    chunk_index: int
    metadata: dict = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    sources: list[str] = Field(default_factory=list)
    limit: int = Field(default=8, ge=1, le=20)


class Citation(BaseModel):
    id: str
    source: str
    title: str
    excerpt: str
    url: str | None = None


class SearchResult(Citation):
    score: float
    document_id: str
    author: str | None = None
    chunk_index: int


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation]
    results: list[SearchResult]
    grounded: bool
    mode: str
    notice: str | None = None
