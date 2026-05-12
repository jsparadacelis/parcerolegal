"""Qdrant Cloud adapter — implements VectorStore port."""

from __future__ import annotations

from qdrant_client import QdrantClient

from backend.app.domain.entities import RetrievedChunk


class QdrantVectorStore:
    def __init__(self, url: str, api_key: str, collection: str) -> None:
        self._collection = collection
        self._client = QdrantClient(url=url, api_key=api_key)

    def search(self, embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
        results = self._client.search(
            collection_name=self._collection,
            query_vector=embedding,
            limit=top_k,
        )
        return [self._to_chunk(point) for point in results]

    def _to_chunk(self, point) -> RetrievedChunk:
        payload = point.payload
        metadata = {k: v for k, v in payload.items() if k not in ("text", "source_type")}
        return RetrievedChunk(
            chunk_id=str(point.id),
            text=payload["text"],
            score=point.score,
            source_type=payload["source_type"],
            metadata=metadata,
        )
