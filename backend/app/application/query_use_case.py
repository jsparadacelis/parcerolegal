"""Use case: answer a legal question using RAG."""

from __future__ import annotations

from backend.app.domain.entities import QueryResult
from backend.app.domain.ports import Embedder, LLMClient, VectorStore


class QueryUseCase:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        llm: LLMClient,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._llm = llm

    def execute(self, question: str) -> QueryResult:
        raise NotImplementedError("RAG pipeline implementation pending")
