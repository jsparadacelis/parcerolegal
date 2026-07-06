"""Pydantic DTOs for the API layer — separate from domain entities."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from backend.app.infrastructure.config import QUESTION_MAX_LENGTH, QUESTION_MIN_LENGTH


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=QUESTION_MIN_LENGTH, max_length=QUESTION_MAX_LENGTH)

    @field_validator("question", mode="before")
    @classmethod
    def strip_whitespace(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


class SourceResponse(BaseModel):
    chunk_id: str
    source_type: str
    title: str
    url: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    out_of_scope: bool = False
    processing_time_ms: float


class HealthResponse(BaseModel):
    status: str
    environment: str


class ErrorResponse(BaseModel):
    detail: str
