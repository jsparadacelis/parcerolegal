"""API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_use_case
from backend.app.api.schemas import QueryRequest, QueryResponse, SourceResponse
from backend.app.application.query_use_case import QueryUseCase

router = APIRouter()


@router.post("/api/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    use_case: QueryUseCase = Depends(get_use_case),
) -> QueryResponse:
    result = use_case.execute(request.question)
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
