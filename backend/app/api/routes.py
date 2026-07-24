"""API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.dependencies import get_share_use_case, get_shared_answer_store, get_use_case
from backend.app.api.schemas import (
    QueryRequest,
    QueryResponse,
    ShareRequest,
    SharedAnswerResponse,
    ShareResponse,
    SourceResponse,
)
from backend.app.application.query_use_case import QueryUseCase
from backend.app.application.share_answer_use_case import ShareAnswerUseCase
from backend.app.domain.ports import SharedAnswerStore

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
    )


@router.post("/api/shares", response_model=ShareResponse, status_code=201)
def create_share(
    request: ShareRequest,
    use_case: ShareAnswerUseCase = Depends(get_share_use_case),
) -> ShareResponse:
    share_id = use_case.execute(request.question)
    logger.info("share created id=%s question_len=%d", share_id, len(request.question))
    return ShareResponse(id=share_id)


@router.get("/api/shares/{share_id}", response_model=SharedAnswerResponse)
def get_share(
    share_id: str,
    store: SharedAnswerStore = Depends(get_shared_answer_store),
) -> SharedAnswerResponse:
    shared = store.get(share_id)
    if shared is None:
        raise HTTPException(status_code=404, detail="Enlace no encontrado.")
    return SharedAnswerResponse(
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
