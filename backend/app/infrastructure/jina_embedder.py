"""Jina AI embedder — implements Embedder port via direct HTTP."""

from __future__ import annotations

import time
from collections.abc import Callable

from backend.app.infrastructure.config import (
    HTTP_TOO_MANY_REQUESTS,
    HTTP_TRANSIENT_SERVER_ERRORS,
    JINA_EMBEDDING_TASK,
    JINA_EMBEDDINGS_URL,
    JINA_MAX_RETRIES,
    JINA_MAX_RETRY_WAIT_SECONDS,
    JINA_RETRY_BASE_DELAY_SECONDS,
    JINA_TIMEOUT_SECONDS,
)
from backend.app.infrastructure.http_retry import RetryPolicy, post_with_retries

_RETRY_POLICY = RetryPolicy(
    max_attempts=JINA_MAX_RETRIES,
    base_delay_seconds=JINA_RETRY_BASE_DELAY_SECONDS,
    max_total_wait_seconds=JINA_MAX_RETRY_WAIT_SECONDS,
    retryable_statuses=HTTP_TRANSIENT_SERVER_ERRORS | {HTTP_TOO_MANY_REQUESTS},
)


class JinaEmbedder:
    def __init__(
        self,
        api_key: str,
        model: str,
        dimensions: int,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._model = model
        self._dimensions = dimensions
        self._sleep = sleep
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def embed(self, text: str) -> list[float]:
        payload = {
            "model": self._model,
            "task": JINA_EMBEDDING_TASK,
            "dimensions": self._dimensions,
            "input": [text],
        }
        response = post_with_retries(
            JINA_EMBEDDINGS_URL,
            payload=payload,
            headers=self._headers,
            timeout=JINA_TIMEOUT_SECONDS,
            policy=_RETRY_POLICY,
            sleep=self._sleep,
        )
        return response.json()["data"][0]["embedding"]
