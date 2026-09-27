"""Tests for DeepHealthCheckUseCase — verifica cada dependencia externa en
paralelo y traduce los fallos a mensajes seguros de exponer."""
from __future__ import annotations

import logging
import threading
from unittest.mock import create_autospec

import pytest
import requests

from backend.app.application.deep_health_check_use_case import DeepHealthCheckUseCase
from backend.app.domain.entities import DependencyStatus
from backend.app.domain.ports import DependencyCheckError, DependencyProbe

_LEAKY_URL = "https://admin:super-secret@proj.supabase.co/rest/v1/queries"
_CACHE_TTL_SECONDS = 30.0


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def qdrant_probe() -> DependencyProbe:
    return create_autospec(DependencyProbe, spec_set=True, instance=True)


@pytest.fixture
def groq_probe() -> DependencyProbe:
    return create_autospec(DependencyProbe, spec_set=True, instance=True)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def use_case(qdrant_probe, groq_probe, clock) -> DeepHealthCheckUseCase:
    return DeepHealthCheckUseCase(
        probes={"qdrant": qdrant_probe, "groq": groq_probe, "supabase": None},
        cache_ttl_seconds=_CACHE_TTL_SECONDS,
        clock=clock,
    )


class TestExecute:
    def test_reports_every_configured_dependency(self, use_case):
        report = use_case.execute()

        assert set(report.checks) == {"qdrant", "groq", "supabase"}

    def test_healthy_when_every_probe_passes(self, use_case):
        report = use_case.execute()

        assert report.is_healthy is True
        assert report.checks["qdrant"].ok is True
        assert report.checks["qdrant"].error is None

    def test_records_latency_in_whole_milliseconds(self, use_case):
        report = use_case.execute()

        assert isinstance(report.checks["qdrant"].latency_ms, int)
        assert report.checks["qdrant"].latency_ms >= 0

    def test_unconfigured_dependency_is_skipped(self, use_case):
        report = use_case.execute()

        assert report.checks["supabase"] == DependencyStatus.skipped_check()

    def test_check_error_message_is_exposed(self, use_case, groq_probe):
        groq_probe.check.side_effect = DependencyCheckError("modelo 'x' no disponible")

        report = use_case.execute()

        assert report.is_healthy is False
        assert report.checks["groq"].ok is False
        assert report.checks["groq"].error == "modelo 'x' no disponible"

    def test_one_failure_does_not_hide_the_other_checks(self, use_case, groq_probe):
        groq_probe.check.side_effect = DependencyCheckError("boom")

        report = use_case.execute()

        assert report.checks["qdrant"].ok is True

    def test_unexpected_errors_only_expose_the_exception_type(self, use_case, qdrant_probe):
        qdrant_probe.check.side_effect = requests.ConnectionError(f"Max retries for {_LEAKY_URL}")

        report = use_case.execute()

        assert report.checks["qdrant"].error == "ConnectionError"

    def test_failures_are_logged_without_secrets(self, use_case, qdrant_probe, caplog):
        qdrant_probe.check.side_effect = requests.ConnectionError(f"Max retries for {_LEAKY_URL}")

        with caplog.at_level(logging.WARNING, logger="parcerolegal"):
            use_case.execute()

        assert "qdrant" in caplog.text
        assert "super-secret" not in caplog.text

    def test_runs_probes_in_parallel(self, use_case, qdrant_probe, groq_probe):
        # Si los probes corrieran en serie, el primero esperaría al segundo en
        # la barrera hasta el timeout y fallaría con BrokenBarrierError.
        barrier = threading.Barrier(2, timeout=2)
        qdrant_probe.check.side_effect = barrier.wait
        groq_probe.check.side_effect = barrier.wait

        report = use_case.execute()

        assert report.is_healthy is True


class TestCache:
    def test_reuses_the_report_within_the_ttl(self, use_case, qdrant_probe, clock):
        use_case.execute()
        clock.now += _CACHE_TTL_SECONDS - 1

        use_case.execute()

        assert qdrant_probe.check.call_count == 1

    def test_probes_again_after_the_ttl(self, use_case, qdrant_probe, clock):
        use_case.execute()
        clock.now += _CACHE_TTL_SECONDS + 1

        use_case.execute()

        assert qdrant_probe.check.call_count == 2
