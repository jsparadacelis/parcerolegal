"""Tests for domain entities."""

import pytest

from backend.app.domain.entities import QueryResult, RetrievedChunk, Source


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


class TestQueryResult:
    def test_out_of_scope_result(self):
        result = QueryResult(
            answer="No se encontraron resultados relevantes.",
            sources=[],
            out_of_scope=True,
            processing_time_ms=120.5,
        )
        assert result.out_of_scope is True
        assert result.sources == []

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
        )
        assert len(result.sources) == 1
        assert result.out_of_scope is False
