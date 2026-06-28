"""FastAPI application."""

from __future__ import annotations

import logging
import time

import requests
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.dependencies import get_settings
from backend.app.api.routes import router
from backend.app.api.schemas import HealthResponse
from backend.app.infrastructure.config import Settings

logger = logging.getLogger("parcerolegal")

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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed_ms = (time.time() - start) * 1000
    logger.info("%s %s %s %.0fms", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


@app.exception_handler(requests.exceptions.Timeout)
async def timeout_handler(request: Request, exc: requests.exceptions.Timeout) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "El servicio tardó demasiado en responder. Por favor intenta de nuevo."},
    )


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled exception: %s: %s", type(exc).__name__, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
    )


app.include_router(router)


@app.get("/api/health", response_model=HealthResponse)
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)
