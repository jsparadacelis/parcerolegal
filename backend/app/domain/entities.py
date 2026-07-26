"""Domain entities — pure Python dataclasses, no framework imports."""

from __future__ import annotations

from dataclasses import dataclass, field

# Tipos de fuente del corpus. Determinan cómo se construye el título/URL de una Source.
SOURCE_TYPE_CONSTITUCION = "constitucion"
SOURCE_TYPE_SENTENCIA = "sentencia"
SOURCE_TYPE_CODIGO_PENAL = "codigo_penal"
SOURCE_TYPE_CODIGO_SUSTANTIVO_TRABAJO = "codigo_sustantivo_trabajo"


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    source_type: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Source:
    chunk_id: str
    source_type: str
    title: str
    url: str


@dataclass(frozen=True)
class QueryResult:
    """`share_token` identifica este registro para compartirlo sin volver a
    llamar al RAG: lo genera QueryUseCase.execute() y es el mismo valor que
    queda guardado en el QueryLog correspondiente (ver ese docstring)."""

    answer: str
    sources: list[Source]
    out_of_scope: bool
    processing_time_ms: float
    share_token: str


@dataclass(frozen=True)
class QueryLog:
    """Un registro de TODAS las consultas respondidas, persistido best-effort.

    Se guardan todas las consultas (no solo las que caen bajo el umbral de
    similitud) para poder analizar tanto vacíos del corpus como respuestas en
    alcance. `out_of_scope` indica si cayó bajo el umbral. `top_score` es la
    mayor similitud recuperada antes de filtrar (None si no hubo chunks): permite
    distinguir el near-miss del ruido y recalibrar el umbral. `sources` son las
    fuentes citadas en la respuesta ([] si out_of_scope).

    `share_token` es lo que hace posible compartir sin volver a llamar al RAG:
    se genera en QueryUseCase.execute() (no en este registro) y es el mismo
    valor que se devuelve al cliente en QueryResult — un lookup posterior por
    ese token (GetSharedQueryUseCase/QueryLogFinder) encuentra este registro
    exacto, ya persistido, sin recalcular nada.
    """

    question: str
    answer: str
    sources: list[Source]
    top_score: float | None
    detected_area: str | None
    out_of_scope: bool
    share_token: str
