"""Jina AI embedder — implements Embedder port via direct HTTP."""

from __future__ import annotations

import requests

from backend.app.infrastructure.config import (
    JINA_EMBEDDING_TASK,
    JINA_EMBEDDINGS_URL,
    JINA_TIMEOUT_SECONDS,
)


class JinaEmbedder:
    def __init__(self, api_key: str, model: str, dimensions: int) -> None:
        self._model = model
        self._dimensions = dimensions
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def embed(self, text: str) -> list[float]:
        payload = {
            "model": self._model,
            "task": JINA_EMBEDDING_TASK,
            "dimensions": self._dimensions,
            "input": [text],
        }
        response = requests.post(
            JINA_EMBEDDINGS_URL, json=payload, headers=self._headers, timeout=JINA_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
