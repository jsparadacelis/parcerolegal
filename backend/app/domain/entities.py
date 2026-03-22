"""Domain entities — pure Python dataclasses, no framework imports."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    source_type: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Source:
    chunk_id: str
    source_type: str
    title: str
    url: str


@dataclass(frozen=True)
class QueryResult:
    answer: str
    sources: list[Source]
    out_of_scope: bool
    processing_time_ms: float
