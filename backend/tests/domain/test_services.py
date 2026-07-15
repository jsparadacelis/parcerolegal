"""Tests for domain services — score filtering and out-of-scope detection."""

from backend.app.domain.entities import RetrievedChunk, Source
from backend.app.domain.services import (
    dedupe_sources,
    detect_legal_area,
    extract_sentencia_id,
    filter_by_score,
    is_out_of_scope,
)


def _chunk(score: float, chunk_id: str = "c1") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id, text="text", score=score, source_type="constitucion"
    )


def a_sentencia_source(chunk_id: str = "c1", sentencia_id: str = "T-622-16") -> Source:
    return Source(
        chunk_id=chunk_id,
        source_type="sentencia",
        title=sentencia_id,
        url=f"http://corte.gov.co/{sentencia_id}",
    )


def a_constitucion_source(chunk_id: str = "c1", article: str = "30") -> Source:
    return Source(
        chunk_id=chunk_id,
        source_type="constitucion",
        title=f"Art. {article} — Título",
        url=f"http://example.com/art{article}",
    )


class TestFilterByScore:
    def test_all_above_threshold(self):
        chunks = [_chunk(0.80), _chunk(0.90)]

        assert len(filter_by_score(chunks)) == 2

    def test_all_below_threshold(self):
        chunks = [_chunk(0.30), _chunk(0.39)]

        assert len(filter_by_score(chunks)) == 0

    def test_mixed_scores(self):
        chunks = [_chunk(0.80, "high"), _chunk(0.30, "low"), _chunk(0.70, "mid")]

        result = filter_by_score(chunks)

        ids = [c.chunk_id for c in result]
        assert len(result) == 2
        assert "high" in ids
        assert "mid" in ids
        assert "low" not in ids

    def test_exact_threshold_included(self):
        chunks = [_chunk(0.40)]

        assert len(filter_by_score(chunks)) == 1

    def test_just_below_threshold_excluded(self):
        chunks = [_chunk(0.399)]

        assert len(filter_by_score(chunks)) == 0

    def test_empty_input(self):
        assert filter_by_score([]) == []

    def test_custom_threshold(self):
        chunks = [_chunk(0.50), _chunk(0.60)]

        result = filter_by_score(chunks, threshold=0.55)

        assert len(result) == 1
        assert result[0].score == 0.60


class TestIsOutOfScope:
    def test_empty_list_is_out_of_scope(self):
        assert is_out_of_scope([]) is True

    def test_non_empty_list_is_not_out_of_scope(self):
        assert is_out_of_scope([_chunk(0.80)]) is False


class TestDetectLegalArea:
    def test_divorce_maps_to_civil_code(self):
        area = detect_legal_area("¿puede mi mujer quedarse con todo tras el divorcio?")

        assert area is not None
        assert "Civil" in area

    def test_labor_dismissal_maps_to_labor_code(self):
        area = detect_legal_area("¿Me pueden despedir sin justa causa?")

        assert area is not None
        assert "Trabajo" in area

    def test_criminal_topic_maps_to_penal_code(self):
        area = detect_legal_area("¿qué pena tiene el hurto?")

        assert area is not None
        assert "Penal" in area

    def test_constitutional_question_returns_none(self):
        assert detect_legal_area("¿qué es la acción de tutela?") is None

    def test_unknown_topic_returns_none(self):
        assert detect_legal_area("cuánto cuesta un carro en Colombia") is None


class TestExtractSentenciaId:
    def test_full_id_with_de_year(self):
        assert extract_sentencia_id("¿Qué dice la sentencia T-760 de 2008?") == "T-760-08"

    def test_su_prefix(self):
        assert extract_sentencia_id("¿Qué dice la sentencia SU-214 de 2016?") == "SU-214-16"

    def test_id_with_short_year_attached_by_hyphen(self):
        assert extract_sentencia_id("¿Qué establece C-355-06 sobre el aborto?") == "C-355-06"

    def test_id_with_short_year_attached_by_slash(self):
        assert extract_sentencia_id("¿Qué dice T-760/08?") == "T-760-08"

    def test_lowercase_input(self):
        assert extract_sentencia_id("sentencia t-760 de 2008") == "T-760-08"

    def test_no_sentencia_mentioned_returns_none(self):
        assert extract_sentencia_id("¿Qué es el habeas corpus?") is None

    def test_id_without_any_year_returns_none(self):
        assert extract_sentencia_id("¿Qué dice T-760?") is None


class TestDedupeSources:
    def test_collapses_duplicate_keeping_first_in_order(self):
        sources = [
            a_sentencia_source(chunk_id="s1", sentencia_id="T-622-16"),
            a_constitucion_source(chunk_id="a1", article="44"),
            a_sentencia_source(chunk_id="s2", sentencia_id="T-622-16"),
        ]

        result = dedupe_sources(sources)

        assert [s.chunk_id for s in result] == ["s1", "a1"]

    def test_keeps_all_distinct_documents(self):
        sources = [
            a_sentencia_source(sentencia_id="T-622-16"),
            a_constitucion_source(article="44"),
            a_sentencia_source(sentencia_id="C-355-06"),
        ]

        result = dedupe_sources(sources)

        assert len(result) == 3

    def test_empty_list_returns_empty(self):
        assert dedupe_sources([]) == []
