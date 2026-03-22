"""Shared test fixtures — Fakes that implement domain ports."""

from __future__ import annotations

import pytest

from backend.app.domain.entities import RetrievedChunk


class FakeEmbedder:
    """Returns a fixed embedding vector."""

    def embed(self, text: str) -> list[float]:
        return [0.1] * 384


class FakeVectorStore:
    """Returns pre-configured chunks."""

    def __init__(self, chunks: list[RetrievedChunk] | None = None) -> None:
        self._chunks = chunks or []

    def search(self, embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
        return self._chunks[:top_k]


class FakeLLMClient:
    """Returns a canned answer."""

    def __init__(self, answer: str = "Respuesta de prueba.") -> None:
        self._answer = answer

    def generate(self, prompt: str) -> str:
        return self._answer


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def fake_store() -> FakeVectorStore:
    return FakeVectorStore()


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    return FakeLLMClient()
