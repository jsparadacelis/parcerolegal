"""Tests for domain services — score filtering and out-of-scope detection."""

from backend.app.domain.entities import RetrievedChunk
from backend.app.domain.services import (
    detect_legal_area,
    extract_sentencia_id,
    filter_by_score,
    is_out_of_scope,
    sanitize_citations,
)


def _chunk(score: float, chunk_id: str = "c1") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id, text="text", score=score, source_type="constitucion"
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


class TestSanitizeCitations:
    def test_no_citations_returns_text_unchanged(self):
        text, invalid = sanitize_citations("No hay citas aquí.", valid_count=5)

        assert text == "No hay citas aquí."
        assert invalid == []

    def test_citations_within_range_are_kept(self):
        text, invalid = sanitize_citations("Igualdad [1] y paz [5].", valid_count=5)

        assert text == "Igualdad [1] y paz [5]."
        assert invalid == []

    def test_citation_of_zero_is_removed(self):
        text, invalid = sanitize_citations("Dato [0]", valid_count=5)

        assert text == "Dato"
        assert invalid == [0]

    def test_multiple_invalid_citations_all_removed(self):
        text, invalid = sanitize_citations(
            "* Igualdad [1], [13]\n* Paz [1], [22]\n* Integridad personal [12]",
            valid_count=5,
        )

        assert text == "* Igualdad [1]\n* Paz [1]\n* Integridad personal"
        assert invalid == [13, 22, 12]

    def test_invalid_citation_between_two_valid_ones_collapses_comma(self):
        text, invalid = sanitize_citations("[1], [13], [3]", valid_count=5)

        assert text == "[1], [3]"
        assert invalid == [13]

    def test_leading_invalid_citation_strips_dangling_comma(self):
        text, invalid = sanitize_citations("[13], [1]", valid_count=5)

        assert text == "[1]"
        assert invalid == [13]
