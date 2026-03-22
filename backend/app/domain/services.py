"""Domain services — pure functions with business logic."""

from __future__ import annotations

from backend.app.domain.entities import RetrievedChunk

SIMILARITY_THRESHOLD = 0.65


def filter_by_score(
    chunks: list[RetrievedChunk],
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[RetrievedChunk]:
    return [c for c in chunks if c.score >= threshold]


def is_out_of_scope(filtered_chunks: list[RetrievedChunk]) -> bool:
    return len(filtered_chunks) == 0
