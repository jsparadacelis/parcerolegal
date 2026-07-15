"""Domain entities — pure Python dataclasses, no framework imports."""

from __future__ import annotations

from dataclasses import dataclass, field

# Tipos de fuente del corpus. Determinan cómo se construye el título/URL de una Source.
SOURCE_TYPE_CONSTITUCION = "constitucion"
SOURCE_TYPE_SENTENCIA = "sentencia"
SOURCE_TYPE_CODIGO_PENAL = "codigo_penal"


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
    answer: str
    sources: list[Source]
    out_of_scope: bool
    processing_time_ms: float


@dataclass(frozen=True)
class MissedQuery:
    """Una pregunta que cayó fuera de alcance (bajo el umbral de similitud).

    Se persiste best-effort para analizar vacíos del corpus. `top_score` es la
    mayor similitud recuperada antes de filtrar (None si no hubo chunks): permite
    distinguir el near-miss del ruido y recalibrar el umbral. La marca de tiempo
    la asigna el almacenamiento (default server-side).
    """

    question: str
    answer: str
    top_score: float | None
    detected_area: str | None
