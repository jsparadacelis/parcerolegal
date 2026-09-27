"""Use case: health check profundo de las dependencias externas.

Corre cada DependencyProbe en paralelo, mide su latencia y traduce cualquier
fallo a un mensaje seguro de exponer. Los errores inesperados (timeout,
conexión) se reducen al nombre de su clase porque su mensaje crudo suele
incluir URLs de los proveedores.

El reporte se cachea un TTL corto: el endpoint es público y cada ejecución
llama a servicios externos (Jina cobra por token).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from backend.app.domain.entities import DependencyStatus, HealthReport
from backend.app.domain.ports import DependencyCheckError, DependencyProbe

logger = logging.getLogger("parcerolegal")


def _run_probe(name: str, probe: DependencyProbe | None) -> DependencyStatus:
    if probe is None:
        return DependencyStatus.skipped_check()
    start = time.perf_counter()
    try:
        probe.check()
        error = None
    except DependencyCheckError as check_error:
        error = str(check_error)
    except Exception as unexpected_error:  # noqa: BLE001 — cualquier fallo es un check fallido
        error = type(unexpected_error).__name__
    latency_ms = round((time.perf_counter() - start) * 1000)
    if error is not None:
        logger.warning("health check %s falló: %s (%dms)", name, error, latency_ms)
    return DependencyStatus(ok=error is None, latency_ms=latency_ms, error=error)


class DeepHealthCheckUseCase:
    def __init__(
        self,
        probes: dict[str, DependencyProbe | None],
        cache_ttl_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._probes = probes
        self._cache_ttl_seconds = cache_ttl_seconds
        self._clock = clock
        self._cached_report: HealthReport | None = None
        self._cached_at = 0.0

    def execute(self) -> HealthReport:
        now = self._clock()
        if self._cached_report is not None and now - self._cached_at < self._cache_ttl_seconds:
            return self._cached_report
        self._cached_report = self._check_all()
        self._cached_at = now
        return self._cached_report

    def _check_all(self) -> HealthReport:
        with ThreadPoolExecutor(max_workers=max(1, len(self._probes)), thread_name_prefix="health") as executor:
            futures = {
                name: executor.submit(_run_probe, name, probe) for name, probe in self._probes.items()
            }
            return HealthReport(checks={name: future.result() for name, future in futures.items()})
