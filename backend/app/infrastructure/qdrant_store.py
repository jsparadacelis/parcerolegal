"""Qdrant Cloud adapter — implements VectorStore port."""

from __future__ import annotations

from backend.app.domain.entities import RetrievedChunk


class QdrantVectorStore:
    def __init__(self, url: str, api_key: str, collection: str) -> None:
        self._url = url
        self._api_key = api_key
        self._collection = collection

    def search(self, embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
        raise NotImplementedError
