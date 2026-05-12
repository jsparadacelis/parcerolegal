"""FastAPI application."""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.dependencies import get_settings
from backend.app.api.routes import router
from backend.app.api.schemas import HealthResponse
from backend.app.infrastructure.config import Settings

app = FastAPI(
    title="Parcerolegal API",
    description="Colombian legal search engine powered by RAG",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/api/health", response_model=HealthResponse)
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)
