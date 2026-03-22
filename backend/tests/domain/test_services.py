"""Tests for domain services — score filtering and out-of-scope detection."""

from backend.app.domain.entities import RetrievedChunk
from backend.app.domain.services import filter_by_score, is_out_of_scope


def _chunk(score: float, chunk_id: str = "c1") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id, text="text", score=score, source_type="constitucion"
    )


class TestFilterByScore:
    def test_all_above_threshold(self):
        chunks = [_chunk(0.80), _chunk(0.90)]
        assert len(filter_by_score(chunks)) == 2

    def test_all_below_threshold(self):
        chunks = [_chunk(0.30), _chunk(0.50)]
        assert len(filter_by_score(chunks)) == 0

    def test_mixed_scores(self):
        chunks = [_chunk(0.80, "high"), _chunk(0.40, "low"), _chunk(0.70, "mid")]
        result = filter_by_score(chunks)
        assert len(result) == 2
        ids = [c.chunk_id for c in result]
        assert "high" in ids
        assert "mid" in ids
        assert "low" not in ids

    def test_exact_threshold_included(self):
        chunks = [_chunk(0.65)]
        assert len(filter_by_score(chunks)) == 1

    def test_just_below_threshold_excluded(self):
        chunks = [_chunk(0.649)]
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
