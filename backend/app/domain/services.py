"""Domain services — pure functions with business logic."""

from __future__ import annotations

import re

from backend.app.domain.entities import RetrievedChunk

SIMILARITY_THRESHOLD = 0.45

_SENTENCIA_PATTERN = re.compile(r"\b(T|C|SU)-(\d+)\b", re.IGNORECASE)
_SHORT_YEAR_PATTERN = re.compile(r"^[-/](\d{2})\b")
_YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")


def filter_by_score(
    chunks: list[RetrievedChunk],
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[RetrievedChunk]:
    return [c for c in chunks if c.score >= threshold]


def is_out_of_scope(filtered_chunks: list[RetrievedChunk]) -> bool:
    return len(filtered_chunks) == 0


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
