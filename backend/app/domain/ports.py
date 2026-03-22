"""Ports (interfaces) that infrastructure must implement."""

from __future__ import annotations

from typing import Protocol

from backend.app.domain.entities import RetrievedChunk


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class VectorStore(Protocol):
    def search(self, embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]: ...


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str: ...
