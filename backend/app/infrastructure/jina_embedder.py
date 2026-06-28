"""Jina AI embedder — implements Embedder port via direct HTTP."""

from __future__ import annotations

import requests

_JINA_URL = "https://api.jina.ai/v1/embeddings"


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
            "task": "retrieval.query",
            "dimensions": self._dimensions,
            "input": [text],
        }
        response = requests.post(_JINA_URL, json=payload, headers=self._headers, timeout=10)
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
