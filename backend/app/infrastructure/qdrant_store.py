"""Qdrant Cloud adapter — implements VectorStore port via direct HTTP."""

from __future__ import annotations

import requests

from backend.app.domain.entities import RetrievedChunk


class QdrantVectorStore:
    def __init__(self, url: str, api_key: str, collection: str) -> None:
        self._url = f"{url}/collections/{collection}/points/search"
        self._headers = {"api-key": api_key, "Content-Type": "application/json"}

    def search(self, embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
        response = requests.post(
            self._url,
            headers=self._headers,
            json={"vector": embedding, "limit": top_k, "with_payload": True},
        )
        response.raise_for_status()
        return [self._to_chunk(point) for point in response.json()["result"]]

    def _to_chunk(self, point: dict) -> RetrievedChunk:
        payload = point["payload"]
        metadata = {k: v for k, v in payload.items() if k not in ("text", "source_type")}
        return RetrievedChunk(
            chunk_id=str(point["id"]),
            text=payload["text"],
            score=point["score"],
            source_type=payload["source_type"],
            metadata=metadata,
        )
