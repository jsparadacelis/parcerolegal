"""POST con reintentos y backoff exponencial, compartido por los adapters HTTP."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import requests

from backend.app.domain.ports import ServiceBusyError
from backend.app.infrastructure.config import (
    HTTP_TOO_MANY_REQUESTS,
    SERVICE_BUSY_RETRY_AFTER_SECONDS,
)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    base_delay_seconds: float
    # Espera acumulada máxima por llamada: el request del usuario tiene un
    # límite de tiempo y no tiene sentido dormir más allá de él.
    max_total_wait_seconds: float
    retryable_statuses: frozenset[int]


def post_with_retries(
    url: str,
    *,
    payload: dict,
    headers: dict[str, str],
    timeout: float,
    policy: RetryPolicy,
    sleep: Callable[[float], None],
) -> requests.Response:
    """Devuelve la primera respuesta exitosa.

    Estados no reintentables → `requests.HTTPError` inmediato. Reintentos
    agotados por 429 → `ServiceBusyError`; por 5xx → `requests.HTTPError`.
    """
    waited_seconds = 0.0
    for attempt in range(policy.max_attempts):
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if response.status_code not in policy.retryable_statuses:
            response.raise_for_status()
            return response

        delay_seconds = _retry_after_seconds(response) or policy.base_delay_seconds * (2 ** attempt)
        is_last_attempt = attempt == policy.max_attempts - 1
        if is_last_attempt or waited_seconds + delay_seconds > policy.max_total_wait_seconds:
            break
        sleep(delay_seconds)
        waited_seconds += delay_seconds

    _raise_exhausted(response)


def _retry_after_seconds(response: requests.Response) -> float | None:
    """Solo se soporta la forma en segundos; la forma HTTP-date se ignora."""
    raw_value = response.headers.get("Retry-After")
    if raw_value is None:
        return None
    try:
        seconds = float(raw_value)
    except ValueError:
        return None
    return seconds if seconds > 0 else None


def _raise_exhausted(response: requests.Response) -> None:
    if response.status_code == HTTP_TOO_MANY_REQUESTS:
        provider_retry_after = _retry_after_seconds(response)
        retry_after = (
            math.ceil(provider_retry_after) if provider_retry_after else SERVICE_BUSY_RETRY_AFTER_SECONDS
        )
        raise ServiceBusyError(retry_after_seconds=retry_after)
    response.raise_for_status()
