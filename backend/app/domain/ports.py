"""Ports (interfaces) that infrastructure must implement."""

from __future__ import annotations

from typing import Protocol

from backend.app.domain.entities import MissedQuery, RetrievedChunk, SharedAnswer


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


class SharedAnswerStore(Protocol):
    """Persiste una respuesta publicada bajo un link compartible.

    A diferencia de MissedQueryStore, NO es fire-and-forget: `save` debe
    propagar sus errores. Un link compartible roto (por un fallo tragado en
    silencio) es peor que un error visible al usuario que intenta compartir.
    """

    def save(self, shared: SharedAnswer) -> None: ...


class SharedAnswerFinder(Protocol):
    """Busca una respuesta publicada por su share_id.

    Separado de SharedAnswerStore (ver ese docstring): quien solo necesita
    leer un share (GET /api/shares/{id}) no debería depender de un método
    `save` que nunca usa, ni viceversa. Igual que `save`, `get` propaga sus
    errores en vez de tragarlos.
    """

    def get(self, share_id: str) -> SharedAnswer | None: ...
