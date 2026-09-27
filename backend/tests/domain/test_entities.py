"""Tests for domain entities."""

import pytest

from backend.app.domain.entities import (
    SOURCE_TYPE_CODIGO_PENAL,
    SOURCE_TYPE_CODIGO_SUSTANTIVO_TRABAJO,
    SOURCE_TYPE_CONSTITUCION,
    SOURCE_TYPE_SENTENCIA,
    DependencyStatus,
    HealthReport,
    QueryLog,
    QueryResult,
    RetrievedChunk,
    Source,
)


class TestSourceTypeConstants:
    def test_codigo_penal_value(self):
        assert SOURCE_TYPE_CODIGO_PENAL == "codigo_penal"

    def test_codigo_sustantivo_trabajo_value(self):
        assert SOURCE_TYPE_CODIGO_SUSTANTIVO_TRABAJO == "codigo_sustantivo_trabajo"

    def test_all_source_types_are_distinct(self):
        values = {
            SOURCE_TYPE_CONSTITUCION,
            SOURCE_TYPE_SENTENCIA,
            SOURCE_TYPE_CODIGO_PENAL,
            SOURCE_TYPE_CODIGO_SUSTANTIVO_TRABAJO,
        }
        assert len(values) == 4


class TestRetrievedChunk:
    def test_construction(self):
        chunk = RetrievedChunk(
            chunk_id="const-art-13-001",
            text="Todas las personas nacen libres",
            score=0.85,
            source_type="constitucion",
            metadata={"article_numero": 13},
        )

        assert chunk.chunk_id == "const-art-13-001"
        assert chunk.score == 0.85
        assert chunk.metadata["article_numero"] == 13

    def test_frozen_immutability(self):
        chunk = RetrievedChunk(
            chunk_id="c1", text="text", score=0.8, source_type="constitucion"
        )

        with pytest.raises(AttributeError):
            chunk.score = 0.9

    def test_default_metadata_is_empty_dict(self):
        chunk = RetrievedChunk(
            chunk_id="c1", text="text", score=0.8, source_type="constitucion"
        )

        assert chunk.metadata == {}


class TestSource:
    def test_construction(self):
        source = Source(
            chunk_id="sent-T-760-001",
            source_type="sentencia",
            title="T-760-2008",
            url="https://corteconstitucional.gov.co/relatoria/2008/T-760-08.htm",
        )

        assert source.source_type == "sentencia"
        assert source.title == "T-760-2008"


class TestQueryLog:
    def test_construction(self):
        source = Source(
            chunk_id="c1",
            source_type="constitucion",
            title="Art. 30",
            url="https://example.com",
        )

        log = QueryLog(
            question="¿Qué es el habeas corpus?",
            answer="El habeas corpus es un derecho fundamental.",
            sources=[source],
            top_score=0.85,
            detected_area=None,
            out_of_scope=False,
            share_token="kJ3f9xQb2p1",
        )

        assert log.sources == [source]
        assert log.out_of_scope is False
        assert log.share_token == "kJ3f9xQb2p1"

    def test_out_of_scope_has_empty_sources(self):
        log = QueryLog(
            question="¿Cuánto cuesta el arroz?",
            answer="fuera de alcance...",
            sources=[],
            top_score=0.30,
            detected_area=None,
            out_of_scope=True,
            share_token="ab12cd34ef",
        )

        assert log.sources == []

    def test_processing_time_ms_defaults_to_none(self):
        """Filas guardadas antes de la migración 006 no tienen latencia."""
        log = QueryLog(
            question="¿Cuánto cuesta el arroz?",
            answer="fuera de alcance...",
            sources=[],
            top_score=0.30,
            detected_area=None,
            out_of_scope=True,
            share_token="ab12cd34ef",
        )

        assert log.processing_time_ms is None

    def test_carries_processing_time_ms(self):
        log = QueryLog(
            question="¿Qué es el habeas corpus?",
            answer="El habeas corpus es un derecho fundamental.",
            sources=[],
            top_score=0.85,
            detected_area=None,
            out_of_scope=False,
            share_token="kJ3f9xQb2p1",
            processing_time_ms=1834,
        )

        assert log.processing_time_ms == 1834


class TestQueryResult:
    def test_out_of_scope_result(self):
        result = QueryResult(
            answer="No se encontraron resultados relevantes.",
            sources=[],
            out_of_scope=True,
            processing_time_ms=120.5,
            share_token="ab12cd34ef",
        )

        assert result.out_of_scope is True
        assert result.sources == []
        assert result.share_token == "ab12cd34ef"

    def test_successful_result_with_sources(self):
        source = Source(
            chunk_id="c1",
            source_type="constitucion",
            title="Articulo 13",
            url="https://example.com",
        )

        result = QueryResult(
            answer="El articulo 13 establece...",
            sources=[source],
            out_of_scope=False,
            processing_time_ms=350.0,
            share_token="kJ3f9xQb2p1",
        )

        assert len(result.sources) == 1
        assert result.out_of_scope is False
        assert result.share_token == "kJ3f9xQb2p1"


def a_healthy_status() -> DependencyStatus:
    return DependencyStatus(ok=True, latency_ms=120, error=None)


def a_failing_status() -> DependencyStatus:
    return DependencyStatus(ok=False, latency_ms=5000, error="ReadTimeout")


def a_skipped_status() -> DependencyStatus:
    return DependencyStatus(ok=True, latency_ms=0, error=None, skipped=True)


class TestDependencyStatus:
    def test_is_not_skipped_by_default(self):
        assert a_healthy_status().skipped is False

    def test_skipped_factory_is_ok_without_latency(self):
        assert DependencyStatus.skipped_check() == a_skipped_status()


class TestHealthReport:
    def test_is_healthy_when_every_check_is_ok(self):
        report = HealthReport(checks={"qdrant": a_healthy_status(), "groq": a_healthy_status()})

        assert report.is_healthy is True

    def test_is_not_healthy_when_any_check_fails(self):
        report = HealthReport(checks={"qdrant": a_healthy_status(), "groq": a_failing_status()})

        assert report.is_healthy is False

    def test_skipped_checks_do_not_degrade_health(self):
        report = HealthReport(checks={"qdrant": a_healthy_status(), "supabase": a_skipped_status()})

        assert report.is_healthy is True
