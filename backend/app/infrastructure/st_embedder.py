"""Sentence-transformers adapter — implements Embedder port."""

from __future__ import annotations


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError
