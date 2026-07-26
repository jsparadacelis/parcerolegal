"""Ports (interfaces) that infrastructure must implement."""

from __future__ import annotations

from typing import Protocol

from backend.app.domain.entities import QueryLog, RetrievedChunk


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


class QueryLogStore(Protocol):
    """Persistencia best-effort de todas las consultas respondidas.

    Contrato: `save` es fire-and-forget — no debe bloquear la respuesta al
    usuario ni propagar excepciones. El use case además la envuelve de forma
    defensiva, así que un fallo aquí nunca rompe la consulta.
    """

    def save(self, log: QueryLog) -> None: ...


class QueryLogFinder(Protocol):
    """Busca un QueryLog ya persistido por su share_token.

    Separado de QueryLogStore (ISP: quien solo necesita leer un share
    -GET /api/shares/{token}- no debería depender de un método `save` que
    nunca usa, ni viceversa). A diferencia de `save`, `find_by_share_token`
    NO es fire-and-forget: debe propagar sus errores. Un link compartible que
    falla en silencio es peor que un error visible a quien intenta abrirlo.
    """

    def find_by_share_token(self, share_token: str) -> QueryLog | None: ...
