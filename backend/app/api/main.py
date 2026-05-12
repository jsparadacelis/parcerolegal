"""FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.dependencies import get_settings, get_use_case
from backend.app.api.routes import router
from backend.app.api.schemas import HealthResponse
from backend.app.infrastructure.config import Settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_use_case()  # pre-warms sentence-transformers model download
    yield


app = FastAPI(
    title="Parcerolegal API",
    description="Colombian legal search engine powered by RAG",
    version="0.1.0",
    lifespan=lifespan,
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
