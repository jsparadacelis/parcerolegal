"""Ports (interfaces) that infrastructure must implement."""

from __future__ import annotations

from typing import Protocol

from backend.app.domain.entities import MissedQuery, RetrievedChunk


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class VectorStore(Protocol):
    def search(
        self,
        embedding: list[float],
        top_k: int = 5,
        sentencia_id: str | None = None,
    ) -> list[RetrievedChunk]: ...


class LLMClient(Protocol):
    def generate(self, prompt: str, system: str = "") -> str: ...


class MissedQueryStore(Protocol):
    """Persistencia best-effort de todas las consultas respondidas.

    Contrato: `save` es fire-and-forget — no debe bloquear la respuesta al
    usuario ni propagar excepciones. El use case además la envuelve de forma
    defensiva, así que un fallo aquí nunca rompe la consulta.
    """

    def save(self, missed: MissedQuery) -> None: ...
