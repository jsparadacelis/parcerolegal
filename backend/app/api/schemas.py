"""Pydantic DTOs for the API layer — separate from domain entities."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


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
