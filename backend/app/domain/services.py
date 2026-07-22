"""Domain services — pure functions with business logic."""

from __future__ import annotations

import re

from backend.app.domain.entities import RetrievedChunk, Source

# Umbral de similitud para el pre-filtro de fuera-de-alcance.
# Calibrado con scores medidos contra el corpus de producción (jina-embeddings-v3):
#   in-scope borderline  "Como se ponen tutelas"          top=0.446
#   out-of-scope real    "...quedarse con todo tras el divorcio"  top=0.383
#   out-of-scope basura  "cuánto cuesta un carro"          top=0.385
# 0.40 cae en el gap: deja pasar la tutela coloquial y sigue tumbando lo genuinamente
# fuera de alcance. El system prompt del LLM ("Si el contexto no cubre la pregunta,
# di: 'Esta información no está disponible...'") es la segunda red anti-alucinación.
SIMILARITY_THRESHOLD = 0.40

_SENTENCIA_PATTERN = re.compile(r"\b(T|C|SU)-(\d+)\b", re.IGNORECASE)
_SHORT_YEAR_PATTERN = re.compile(r"^[-/](\d{2})\b")
_YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")

_CITATION_PATTERN = re.compile(r"\[(\d+)\]")
_REPEATED_COMMA_PATTERN = re.compile(r",(?:\s*,)+")
_LEADING_DANGLING_COMMA_PATTERN = re.compile(r"^[ \t]*,[ \t]*", re.MULTILINE)
_TRAILING_DANGLING_COMMA_PATTERN = re.compile(r"[ \t]*,[ \t]*$", re.MULTILINE)
_TRAILING_WHITESPACE_PATTERN = re.compile(r"[ \t]+$", re.MULTILINE)

# Áreas del derecho fuera del corpus actual (Constitución + sentencias de la Corte
# + Código Penal Libro II). Orden importa: la primera coincidencia gana. Solo se
# usa para dar contexto en el mensaje de fuera-de-alcance, nunca decide si se
# responde o no.
#
# "derecho penal" se retiró de aquí el 2026-07-15: el Código Penal (Libro II,
# Parte Especial) entró al corpus, así que preguntas sobre delitos ya no son
# fuera de alcance — deben resolverse por retrieval normal. El Libro I (Parte
# General: dolo/culpa, tentativa, agravantes genéricos) NO se ingirió y sigue
# fuera de alcance, pero sin categoría propia — cae en el mensaje genérico.
_LEGAL_AREAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "derecho de familia y sucesiones (regulado por el Código Civil)",
        (
            "divorcio", "sociedad conyugal", "bienes conyugales", "gananciales",
            "herencia", "sucesión", "sucesion", "matrimonio", "custodia",
            "patria potestad", "cuota alimentaria",
        ),
    ),
    (
        "derecho laboral (regulado por el Código Sustantivo del Trabajo)",
        (
            "despedir", "despido", "sin justa causa", "contrato de trabajo",
            "liquidación laboral", "cesantías", "cesantias", "prestaciones sociales",
            "acoso laboral", "indemnización laboral",
        ),
    ),
    (
        "derecho comercial o de contratos (Código de Comercio / Código Civil)",
        (
            "arriendo", "arrendamiento", "compraventa", "cobro de cartera",
            "sociedad comercial", "factura",
        ),
    ),
)


def filter_by_score(
    chunks: list[RetrievedChunk],
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[RetrievedChunk]:
    return [c for c in chunks if c.score >= threshold]


def dedupe_sources(sources: list[Source]) -> list[Source]:
    """Colapsa fuentes que apuntan al mismo documento.

    Un documento (un artículo de la Constitución o una sentencia) suele estar
    troceado en varios chunks; si dos de ellos se recuperan, el usuario vería dos
    tarjetas idénticas (mismo título y URL), gastando un espacio de la lista de
    fuentes sin aportar nada. Conserva la primera aparición —la de mayor score,
    porque los chunks llegan ordenados por relevancia— y descarta las repetidas,
    preservando el orden. No toca el contexto que se le pasa al LLM.
    """
    seen: set[tuple[str, str, str]] = set()
    unique: list[Source] = []
    for source in sources:
        key = (source.source_type, source.title, source.url)
        if key in seen:
            continue
        seen.add(key)
        unique.append(source)
    return unique


def detect_legal_area(question: str) -> str | None:
    """Devuelve el área del derecho probable de la pregunta, o None si no se reconoce.

    Heurística de keywords, sin llamar al LLM. Permite construir un mensaje de
    fuera-de-alcance que reconozca el tema y oriente a dónde acudir.
    """
    q = question.lower()
    for area, keywords in _LEGAL_AREAS:
        if any(keyword in q for keyword in keywords):
            return area
    return None


def is_out_of_scope(filtered_chunks: list[RetrievedChunk]) -> bool:
    return len(filtered_chunks) == 0


def sanitize_citations(answer: str, valid_count: int) -> tuple[str, list[int]]:
    """Remueve citas `[n]` fuera del rango 1..valid_count y limpia la puntuación
    huérfana que deja la remoción (comas duplicadas o colgantes, espacios sobrantes).

    Devuelve el texto saneado y la lista de índices inválidos encontrados, en
    orden de aparición — esta última sirve para loguear/medir alucinaciones.
    """
    invalid: list[int] = []

    def _replace(match: re.Match[str]) -> str:
        n = int(match.group(1))
        if 1 <= n <= valid_count:
            return match.group(0)
        invalid.append(n)
        return ""

    sanitized = _CITATION_PATTERN.sub(_replace, answer)
    if not invalid:
        return sanitized, invalid

    sanitized = _REPEATED_COMMA_PATTERN.sub(",", sanitized)
    sanitized = _LEADING_DANGLING_COMMA_PATTERN.sub("", sanitized)
    sanitized = _TRAILING_DANGLING_COMMA_PATTERN.sub("", sanitized)
    sanitized = _TRAILING_WHITESPACE_PATTERN.sub("", sanitized)
    return sanitized, invalid


def is_single_document_answer(sources: list[Source]) -> bool:
    """Verdadero cuando hay 2+ fuentes y todas apuntan al mismo documento.

    Señal de que el retrieval no encontró diversidad real de contenido: el
    `top_k` completo (pensado para traer fragmentos diversos) colapsó en un
    solo documento (p.ej. una sola sentencia), lo que sugiere que el corpus no
    cubre el tema en general y lo recuperado coincidió por cercanía semántica
    puntual. Una sola fuente no cuenta — ahí sí es normal y esperado que un
    único documento responda bien la pregunta.
    """
    if len(sources) < 2:
        return False
    keys = {(s.source_type, s.title, s.url) for s in sources}
    return len(keys) == 1


def extract_sentencia_id(question: str) -> str | None:
    match = _SENTENCIA_PATTERN.search(question)
    if not match:
        return None

    tipo, numero = match.group(1).upper(), match.group(2)
    remainder = question[match.end():]

    short_year_match = _SHORT_YEAR_PATTERN.match(remainder)
    if short_year_match:
        return f"{tipo}-{numero}-{short_year_match.group(1)}"

    year_match = _YEAR_PATTERN.search(question)
    if year_match:
        return f"{tipo}-{numero}-{year_match.group(0)[-2:]}"

    return None
