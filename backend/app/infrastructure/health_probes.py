"""Probes del health check profundo — implementan DependencyProbe vía HTTP directo.

Cada probe hace la llamada más barata que demuestra que la dependencia sirve
para el pipeline real (no solo que el host responde), con timeout corto. Los
errores HTTP se traducen a DependencyCheckError("HTTP <código>") en vez de
propagar requests.HTTPError, cuyo mensaje incluye la URL completa.
"""

from __future__ import annotations

import requests

from backend.app.domain.ports import DependencyCheckError
from backend.app.infrastructure.config import (
    GROQ_MODELS_URL,
    HEALTH_CHECK_TIMEOUT_SECONDS,
    JINA_EMBEDDING_TASK,
    JINA_EMBEDDINGS_URL,
    QDRANT_COLLECTION_PATH,
)

_JINA_PING_INPUT = "ping"
_QDRANT_UNHEALTHY_STATUS = "red"


def _ensure_success(response: requests.Response) -> None:
    if not response.ok:
        raise DependencyCheckError(f"HTTP {response.status_code}")


def _bearer_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


class QdrantProbe:
    """La colección existe, no está en rojo y tiene puntos indexados."""

    def __init__(self, url: str, api_key: str, collection: str) -> None:
        self._collection = collection
        self._url = f"{url}{QDRANT_COLLECTION_PATH.format(collection=collection)}"
        self._headers = {"api-key": api_key}

    def check(self) -> None:
        response = requests.get(self._url, headers=self._headers, timeout=HEALTH_CHECK_TIMEOUT_SECONDS)
        _ensure_success(response)
        collection_info = response.json()["result"]
        if collection_info.get("status") == _QDRANT_UNHEALTHY_STATUS:
            raise DependencyCheckError(f"la colección '{self._collection}' está en estado red")
        if not collection_info.get("points_count"):
            raise DependencyCheckError(f"la colección '{self._collection}' no tiene puntos")


class JinaProbe:
    """Embedding de una palabra: valida API key, modelo y saldo por ~1 token."""

    def __init__(self, api_key: str, model: str, dimensions: int) -> None:
        self._model = model
        self._dimensions = dimensions
        self._headers = _bearer_headers(api_key)

    def check(self) -> None:
        payload = {
            "model": self._model,
            "task": JINA_EMBEDDING_TASK,
            "dimensions": self._dimensions,
            "input": [_JINA_PING_INPUT],
        }
        response = requests.post(
            JINA_EMBEDDINGS_URL, json=payload, headers=self._headers, timeout=HEALTH_CHECK_TIMEOUT_SECONDS
        )
        _ensure_success(response)
        if not response.json()["data"][0]["embedding"]:
            raise DependencyCheckError("Jina devolvió un embedding vacío")


class GroqProbe:
    """El modelo configurado sigue en el catálogo — sin generar tokens."""

    def __init__(self, api_key: str, model: str) -> None:
        self._model = model
        self._headers = _bearer_headers(api_key)

    def check(self) -> None:
        response = requests.get(GROQ_MODELS_URL, headers=self._headers, timeout=HEALTH_CHECK_TIMEOUT_SECONDS)
        _ensure_success(response)
        available_models = {model["id"] for model in response.json()["data"]}
        if self._model not in available_models:
            raise DependencyCheckError(f"el modelo '{self._model}' no está disponible en Groq")


class SupabaseProbe:
    """La tabla del log de consultas es legible (proyecto no pausado)."""

    def __init__(self, url: str, api_key: str, table: str) -> None:
        self._table_url = f"{url.rstrip('/')}/rest/v1/{table}"
        self._headers = {"apikey": api_key, **_bearer_headers(api_key)}

    def check(self) -> None:
        response = requests.get(
            self._table_url,
            headers=self._headers,
            params={"select": "share_token", "limit": 1},
            timeout=HEALTH_CHECK_TIMEOUT_SECONDS,
        )
        _ensure_success(response)
