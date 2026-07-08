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
from backend.app.infrastructure.config import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    CORS_ALLOW_ORIGINS,
    HTTP_SERVICE_UNAVAILABLE,
    SERVICE_TIMEOUT_MESSAGE,
    Settings,
)

logger = logging.getLogger("parcerolegal")

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
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
        status_code=HTTP_SERVICE_UNAVAILABLE,
        content={"detail": SERVICE_TIMEOUT_MESSAGE},
    )


app.include_router(router)


@app.get("/api/health", response_model=HealthResponse)
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)
