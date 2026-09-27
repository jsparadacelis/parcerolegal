"""Load test de POST /api/query: p50/p95/p99/max, tasa de error y cold start.

Uso:
    python -m backend.scripts.load_test --url https://parcerolegal-production.up.railway.app \\
        --requests 50 --concurrency 10

La primera request se manda sola, antes que el resto, para medir el cold
start sin competencia; el resto sale con `--concurrency` requests en vuelo.
`--concurrency 1` es una corrida secuencial.

Cada consulta queda guardada en la tabla `queries` de ese entorno (no hay
forma de marcarla sin alterar la pregunta y con ello el retrieval): el
reporte imprime el rango horario UTC y las preguntas usadas para poder
excluirlas en docs/latencia-p95.sql.

Los percentiles usan interpolación lineal, igual que `percentile_cont` de
Postgres, para que sean comparables con los de producción.
"""

from __future__ import annotations

import argparse
import asyncio
import math
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

DEFAULT_CONCURRENCY = 10
DEFAULT_REQUESTS = 50
DEFAULT_TIMEOUT_SECONDS = 90.0
_QUERY_PATH = "/api/query"
_HTTP_OK = 200

# Variadas a propósito: constitución, tutela/sentencias, laboral, penal y
# fuera de alcance (que no llega al LLM y por eso se reporta aparte).
LOAD_TEST_QUESTIONS: tuple[str, ...] = (
    "¿Qué es el habeas corpus y cuándo procede?",
    "¿Cómo interpongo una acción de tutela si la EPS me niega un medicamento?",
    "¿Me pueden despedir sin justa causa y qué indemnización me corresponde?",
    "¿Cuál es la pena por el delito de hurto en Colombia?",
    "¿Qué dice la Constitución sobre la libertad de expresión?",
    "¿Qué dijo la Corte Constitucional en la sentencia T-760 de 2008 sobre el derecho a la salud?",
    "¿Cuántos días de vacaciones remuneradas tengo al año?",
    "¿Qué pena tiene la violencia intrafamiliar?",
    "¿Qué es el derecho de petición y en cuánto tiempo deben responderlo?",
    "¿Qué es el periodo de prueba en un contrato de trabajo?",
    "¿Cuál es la receta del ajiaco santafereño?",
    "¿Qué derechos tienen las personas desplazadas por la violencia según la Corte?",
)


@dataclass(frozen=True)
class RequestResult:
    """Resultado de una request. `status_code` None = no hubo respuesta
    (timeout, conexión rechazada); `error` guarda el nombre de la excepción."""

    question: str
    status_code: int | None
    latency_ms: float
    server_processing_ms: float | None = None
    out_of_scope: bool | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status_code == _HTTP_OK

    @property
    def status_label(self) -> str:
        return str(self.status_code) if self.status_code is not None else str(self.error)


@dataclass(frozen=True)
class LatencyStats:
    count: int
    p50: float
    p95: float
    p99: float
    max: float


@dataclass(frozen=True)
class LoadTestSummary:
    """`warm*` excluyen el cold start y solo cuentan requests exitosas."""

    total: int
    errors: int
    out_of_scope: int
    status_counts: dict[str, int]
    cold_start: RequestResult
    warm: LatencyStats | None
    warm_in_scope: LatencyStats | None
    warm_server: LatencyStats | None

    @property
    def error_rate(self) -> float:
        return self.errors / self.total


def percentile(values: list[float], fraction: float) -> float:
    """Percentil con interpolación lineal, equivalente a `percentile_cont`."""
    if not values:
        raise ValueError("no se puede calcular un percentil de una lista vacía")
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"el percentil debe estar entre 0 y 1, no {fraction}")
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    weight = position - lower_index
    return ordered[lower_index] + (ordered[upper_index] - ordered[lower_index]) * weight


def latency_stats(values: list[float]) -> LatencyStats | None:
    if not values:
        return None
    return LatencyStats(
        count=len(values),
        p50=percentile(values, 0.50),
        p95=percentile(values, 0.95),
        p99=percentile(values, 0.99),
        max=max(values),
    )


def summarize(results: list[RequestResult]) -> LoadTestSummary:
    if not results:
        raise ValueError("no hay resultados para resumir")
    warm_ok = [result for result in results[1:] if result.ok]
    return LoadTestSummary(
        total=len(results),
        errors=sum(1 for result in results if not result.ok),
        out_of_scope=sum(1 for result in results if result.ok and result.out_of_scope),
        status_counts=dict(Counter(result.status_label for result in results)),
        cold_start=results[0],
        warm=latency_stats([result.latency_ms for result in warm_ok]),
        warm_in_scope=latency_stats(
            [result.latency_ms for result in warm_ok if not result.out_of_scope]
        ),
        warm_server=latency_stats(
            [
                result.server_processing_ms
                for result in warm_ok
                if result.server_processing_ms is not None
            ]
        ),
    )


def format_report(summary: LoadTestSummary) -> str:
    cold_start = summary.cold_start
    status_breakdown = ", ".join(
        f"{label}: {count}" for label, count in sorted(summary.status_counts.items())
    )
    lines = [
        f"Requests: {summary.total}  |  errores: {summary.errors} "
        f"({summary.error_rate:.1%})  |  fuera de alcance: {summary.out_of_scope}",
        f"Códigos: {status_breakdown}",
        f"Cold start (1ra request, sola): {cold_start.latency_ms:.0f} ms "
        f"[{cold_start.status_label}]",
        _format_stats_line("Resto, cliente (todas las exitosas)", summary.warm),
        _format_stats_line("Resto, cliente (solo en alcance)", summary.warm_in_scope),
        _format_stats_line("Resto, servidor (processing_time_ms)", summary.warm_server),
    ]
    return "\n".join(lines)


def _format_stats_line(label: str, stats: LatencyStats | None) -> str:
    if stats is None:
        return f"{label}: sin datos"
    return (
        f"{label} (n={stats.count}): p50 {stats.p50:.0f} ms | p95 {stats.p95:.0f} ms | "
        f"p99 {stats.p99:.0f} ms | max {stats.max:.0f} ms"
    )


def build_questions(total: int) -> list[str]:
    return [LOAD_TEST_QUESTIONS[index % len(LOAD_TEST_QUESTIONS)] for index in range(total)]


def run_load_test(
    base_url: str,
    questions: list[str],
    concurrency: int = DEFAULT_CONCURRENCY,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[RequestResult]:
    """Devuelve los resultados en el orden de `questions`; el primero es el cold start."""
    return asyncio.run(
        _run_all(base_url, questions, concurrency, timeout_seconds, transport)
    )


async def _run_all(
    base_url: str,
    questions: list[str],
    concurrency: int,
    timeout_seconds: float,
    transport: httpx.AsyncBaseTransport | None,
) -> list[RequestResult]:
    if not questions:
        return []
    async with httpx.AsyncClient(
        base_url=base_url, timeout=timeout_seconds, transport=transport
    ) as client:
        cold_start = await _send_query(client, questions[0])
        semaphore = asyncio.Semaphore(concurrency)
        rest = await asyncio.gather(
            *(_send_query_limited(client, semaphore, question) for question in questions[1:])
        )
    return [cold_start, *rest]


async def _send_query_limited(
    client: httpx.AsyncClient, semaphore: asyncio.Semaphore, question: str
) -> RequestResult:
    async with semaphore:
        return await _send_query(client, question)


async def _send_query(client: httpx.AsyncClient, question: str) -> RequestResult:
    start = time.perf_counter()
    try:
        response = await client.post(_QUERY_PATH, json={"question": question})
    except httpx.HTTPError as error:
        return RequestResult(
            question=question,
            status_code=None,
            latency_ms=_elapsed_ms_since(start),
            error=type(error).__name__,
        )
    latency_ms = _elapsed_ms_since(start)
    if response.status_code != _HTTP_OK:
        return RequestResult(question=question, status_code=response.status_code, latency_ms=latency_ms)
    body = response.json()
    return RequestResult(
        question=question,
        status_code=response.status_code,
        latency_ms=latency_ms,
        server_processing_ms=body.get("processing_time_ms"),
        out_of_scope=body.get("out_of_scope"),
    )


def _elapsed_ms_since(start: float) -> float:
    return (time.perf_counter() - start) * 1000


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", required=True, help="URL base del backend")
    parser.add_argument("--requests", type=int, default=DEFAULT_REQUESTS)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    questions = build_questions(args.requests)

    started_at = datetime.now(timezone.utc)
    results = run_load_test(
        args.url, questions, concurrency=args.concurrency, timeout_seconds=args.timeout
    )
    finished_at = datetime.now(timezone.utc)

    print(f"Load test contra {args.url} — {args.requests} requests, concurrencia {args.concurrency}")
    print(f"Rango UTC: {started_at.isoformat(timespec='seconds')} → {finished_at.isoformat(timespec='seconds')}")
    print(format_report(summarize(results)))
    print("Preguntas usadas:")
    for question in sorted(set(questions)):
        print(f"  - {question}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
