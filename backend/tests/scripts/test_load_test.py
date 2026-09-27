"""Tests for backend/scripts/load_test.py — sin red.

El cálculo de percentiles debe coincidir con `percentile_cont` de Postgres
(interpolación lineal) para que el p95 del load test y el de
docs/latencia-p95.sql sean comparables. Las requests HTTP se cortan con
httpx.MockTransport.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest

from backend.scripts.load_test import (
    LOAD_TEST_QUESTIONS,
    LatencyStats,
    RequestResult,
    build_questions,
    format_report,
    latency_stats,
    main,
    percentile,
    run_load_test,
    summarize,
)

_BASE_URL = "https://api.example.com"


def a_result(
    latency_ms: float = 1000.0,
    status_code: int | None = 200,
    server_processing_ms: float | None = 900.0,
    out_of_scope: bool | None = False,
    error: str | None = None,
) -> RequestResult:
    return RequestResult(
        question="¿Qué es el habeas corpus?",
        status_code=status_code,
        latency_ms=latency_ms,
        server_processing_ms=server_processing_ms,
        out_of_scope=out_of_scope,
        error=error,
    )


class _RecordingQueryHandler:
    """Responde como POST /api/query y registra las preguntas recibidas."""

    def __init__(self) -> None:
        self.received: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.received.append(json.loads(request.content)["question"])
        return httpx.Response(
            200,
            json={
                "answer": "respuesta",
                "sources": [],
                "out_of_scope": False,
                "processing_time_ms": 1234.5,
                "share_token": "abc",
            },
        )


def _raise_read_timeout(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("timeout", request=request)


def _respond_429(request: httpx.Request) -> httpx.Response:
    return httpx.Response(429, text="slow down")


@pytest.fixture
def mixed_results() -> list[RequestResult]:
    """Cold start lento + 4 éxitos (uno fuera de alcance) + un 500 + un timeout."""
    return [
        a_result(latency_ms=9000.0, server_processing_ms=8500.0),
        a_result(latency_ms=1000.0),
        a_result(latency_ms=2000.0),
        a_result(latency_ms=3000.0),
        a_result(latency_ms=400.0, server_processing_ms=300.0, out_of_scope=True),
        a_result(latency_ms=5000.0, status_code=500, server_processing_ms=None, out_of_scope=None),
        a_result(
            latency_ms=60000.0,
            status_code=None,
            server_processing_ms=None,
            out_of_scope=None,
            error="ReadTimeout",
        ),
    ]


@pytest.fixture
def query_handler() -> _RecordingQueryHandler:
    return _RecordingQueryHandler()


@pytest.fixture
def ok_transport(query_handler) -> httpx.MockTransport:
    return httpx.MockTransport(query_handler)


class TestPercentile:
    @pytest.mark.parametrize(
        "values,fraction,expected",
        [
            ([1.0, 2.0, 3.0, 4.0], 0.50, 2.5),
            ([float(v) for v in range(1, 21)], 0.95, 19.05),
            ([float(v) for v in range(1, 101)], 0.99, 99.01),
            ([42.0], 0.95, 42.0),
            ([10.0, 20.0], 1.0, 20.0),
            ([10.0, 20.0], 0.0, 10.0),
        ],
    )
    def test_matches_postgres_percentile_cont(self, values, fraction, expected):
        assert percentile(values, fraction) == pytest.approx(expected)

    def test_does_not_depend_on_input_order(self):
        assert percentile([4.0, 1.0, 3.0, 2.0], 0.5) == pytest.approx(2.5)

    def test_raises_on_empty_values(self):
        with pytest.raises(ValueError, match="vací"):
            percentile([], 0.95)

    @pytest.mark.parametrize("fraction", [-0.1, 1.1])
    def test_raises_on_fraction_out_of_range(self, fraction):
        with pytest.raises(ValueError):
            percentile([1.0], fraction)


class TestLatencyStats:
    def test_computes_percentiles_and_max(self):
        stats = latency_stats([float(v) for v in range(1, 21)])

        assert stats == LatencyStats(
            count=20,
            p50=pytest.approx(10.5),
            p95=pytest.approx(19.05),
            p99=pytest.approx(19.81),
            max=20.0,
        )

    def test_returns_none_without_values(self):
        assert latency_stats([]) is None


class TestSummarize:
    def test_separates_cold_start_from_the_rest(self, mixed_results):
        summary = summarize(mixed_results)

        assert summary.cold_start.latency_ms == 9000.0
        assert summary.warm.max == 3000.0

    def test_warm_stats_only_count_successful_requests(self, mixed_results):
        summary = summarize(mixed_results)

        assert summary.warm.count == 4

    def test_in_scope_stats_exclude_out_of_scope_answers(self, mixed_results):
        """Fuera de alcance no llama al LLM: mezclarlas bajaría el p95 real."""
        summary = summarize(mixed_results)

        assert summary.warm_in_scope.count == 3
        assert summary.warm_in_scope.p50 == pytest.approx(2000.0)

    def test_server_stats_use_processing_time_reported_by_backend(self, mixed_results):
        summary = summarize(mixed_results)

        assert summary.warm_server.max == 900.0

    def test_counts_errors_and_status_codes(self, mixed_results):
        summary = summarize(mixed_results)

        assert summary.total == 7
        assert summary.errors == 2
        assert summary.error_rate == pytest.approx(2 / 7)
        assert summary.status_counts == {"200": 5, "500": 1, "ReadTimeout": 1}

    def test_counts_out_of_scope_answers(self, mixed_results):
        assert summarize(mixed_results).out_of_scope == 1

    def test_warm_stats_are_none_when_only_cold_start(self):
        summary = summarize([a_result()])

        assert summary.warm is None
        assert summary.warm_in_scope is None

    def test_raises_without_results(self):
        with pytest.raises(ValueError):
            summarize([])


class TestFormatReport:
    def test_includes_percentiles_cold_start_and_error_rate(self, mixed_results):
        report = format_report(summarize(mixed_results))

        assert "cold start" in report.lower()
        assert "9000" in report
        assert "p95" in report
        assert "28.6%" in report

    def test_includes_status_code_breakdown(self, mixed_results):
        report = format_report(summarize(mixed_results))

        assert "500: 1" in report
        assert "ReadTimeout: 1" in report

    def test_does_not_crash_without_warm_requests(self):
        report = format_report(summarize([a_result()]))

        assert "sin datos" in report


class TestBuildQuestions:
    def test_cycles_through_the_question_set(self):
        questions = build_questions(len(LOAD_TEST_QUESTIONS) + 2)

        assert questions[: len(LOAD_TEST_QUESTIONS)] == list(LOAD_TEST_QUESTIONS)
        assert questions[-2:] == list(LOAD_TEST_QUESTIONS[:2])

    def test_question_set_respects_api_length_limits(self):
        assert all(3 <= len(q) <= 500 for q in LOAD_TEST_QUESTIONS)


class TestRunLoadTest:
    def test_sends_every_question_to_query_endpoint(self, query_handler, ok_transport):
        questions = ["pregunta uno", "pregunta dos", "pregunta tres"]

        results = run_load_test(_BASE_URL, questions, concurrency=2, transport=ok_transport)

        assert sorted(query_handler.received) == sorted(questions)
        assert len(results) == 3

    def test_first_result_is_the_first_question_sent_alone(self, query_handler, ok_transport):
        """El cold start se mide sin competencia: va solo, antes que el resto."""
        questions = ["primera", "segunda", "tercera"]

        results = run_load_test(_BASE_URL, questions, concurrency=3, transport=ok_transport)

        assert query_handler.received[0] == "primera"
        assert results[0].question == "primera"

    def test_records_status_and_server_processing_time(self, ok_transport):
        results = run_load_test(_BASE_URL, ["pregunta"], concurrency=1, transport=ok_transport)

        assert results[0].status_code == 200
        assert results[0].server_processing_ms == 1234.5
        assert results[0].out_of_scope is False
        assert results[0].latency_ms >= 0

    def test_records_http_errors_without_raising(self):
        transport = httpx.MockTransport(_respond_429)

        results = run_load_test(_BASE_URL, ["pregunta"], concurrency=1, transport=transport)

        assert results[0].status_code == 429
        assert results[0].server_processing_ms is None

    def test_records_network_errors_by_exception_name(self):
        transport = httpx.MockTransport(_raise_read_timeout)

        results = run_load_test(_BASE_URL, ["pregunta"], concurrency=1, transport=transport)

        assert results[0].status_code is None
        assert results[0].error == "ReadTimeout"


class TestMain:
    def test_prints_report_and_questions_used(self, capsys, mixed_results):
        with patch("backend.scripts.load_test.run_load_test", return_value=mixed_results) as run:
            exit_code = main(["--url", _BASE_URL, "--requests", "7", "--concurrency", "3"])

        output = capsys.readouterr().out
        assert exit_code == 0
        assert "p95" in output
        assert LOAD_TEST_QUESTIONS[0] in output
        assert run.call_args.kwargs["concurrency"] == 3
        assert len(run.call_args.args[1]) == 7

    def test_defaults_to_concurrency_10(self, mixed_results):
        with patch("backend.scripts.load_test.run_load_test", return_value=mixed_results) as run:
            main(["--url", _BASE_URL])

        assert run.call_args.kwargs["concurrency"] == 10
