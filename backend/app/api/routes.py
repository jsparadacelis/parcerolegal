"""API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.dependencies import get_shared_query_use_case, get_use_case
from backend.app.api.schemas import (
    QueryRequest,
    QueryResponse,
    SharedQueryResponse,
    SourceResponse,
)
from backend.app.application.get_shared_query_use_case import GetSharedQueryUseCase
from backend.app.application.query_use_case import QueryUseCase

logger = logging.getLogger("parcerolegal")

router = APIRouter()


@router.post("/api/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    use_case: QueryUseCase = Depends(get_use_case),
) -> QueryResponse:
    result = use_case.execute(request.question)
    logger.info(
        "query question_len=%d out_of_scope=%s elapsed_ms=%.0f",
        len(request.question),
        result.out_of_scope,
        result.processing_time_ms,
    )
    return QueryResponse(
        answer=result.answer,
        sources=[
            SourceResponse(
                chunk_id=s.chunk_id,
                source_type=s.source_type,
                title=s.title,
                url=s.url,
            )
            for s in result.sources
        ],
        out_of_scope=result.out_of_scope,
        processing_time_ms=result.processing_time_ms,
        share_token=result.share_token,
    )


@router.get("/api/shares/{share_token}", response_model=SharedQueryResponse)
def get_shared_query(
    share_token: str,
    use_case: GetSharedQueryUseCase = Depends(get_shared_query_use_case),
) -> SharedQueryResponse:
    """No vuelve a llamar al RAG: lee directo del log de consultas que
    QueryUseCase ya generó y persistió cuando se respondió la pregunta."""
    shared = use_case.execute(share_token)
    if shared is None:
        raise HTTPException(status_code=404, detail="Enlace no encontrado.")
    return SharedQueryResponse(
        question=shared.question,
        answer=shared.answer,
        sources=[
            SourceResponse(
                chunk_id=s.chunk_id, source_type=s.source_type, title=s.title, url=s.url
            )
            for s in shared.sources
        ],
        out_of_scope=shared.out_of_scope,
    )
