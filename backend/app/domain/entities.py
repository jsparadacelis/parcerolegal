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
    answer: str
    sources: list[Source]
    out_of_scope: bool
    processing_time_ms: float


@dataclass(frozen=True)
class SharedAnswer:
    """Una respuesta publicada bajo un link compartible (GET /api/shares/{id}).

    `id` lo genera el backend (token corto url-safe, ver
    `application.share_answer_use_case`), nunca el cliente: así el contenido
    servido en el link siempre proviene de una ejecución real del pipeline
    RAG, nunca de texto arbitrario enviado por quien comparte.
    """

    id: str
    question: str
    answer: str
    sources: list[Source]
    out_of_scope: bool


@dataclass(frozen=True)
class QueryLog:
    """Un registro de TODAS las consultas respondidas, persistido best-effort.

    Se guardan todas las consultas (no solo las que caen bajo el umbral de
    similitud) para poder analizar tanto vacíos del corpus como respuestas en
    alcance. `out_of_scope` indica si cayó bajo el umbral. `top_score` es la
    mayor similitud recuperada antes de filtrar (None si no hubo chunks): permite
    distinguir el near-miss del ruido y recalibrar el umbral. `sources` son las
    fuentes citadas en la respuesta ([] si out_of_scope). La marca de tiempo la
    asigna el almacenamiento (default server-side).
    """

    question: str
    answer: str
    sources: list[Source]
    top_score: float | None
    detected_area: str | None
    out_of_scope: bool
