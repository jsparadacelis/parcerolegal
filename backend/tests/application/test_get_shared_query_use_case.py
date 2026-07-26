"""Tests for GetSharedQueryUseCase.execute() — busca una consulta ya
respondida por su share_token, sin volver a llamar al pipeline RAG."""
from __future__ import annotations

from unittest.mock import create_autospec

import pytest

from backend.app.application.get_shared_query_use_case import GetSharedQueryUseCase
from backend.app.domain.entities import QueryLog, Source
from backend.app.domain.ports import QueryLogFinder

_SHARE_TOKEN = "kJ3f9xQb2p1"


def a_source() -> Source:
    return Source(
        chunk_id="c1",
        source_type="constitucion",
        title="Art. 30",
        url="https://example.com/art30",
    )


def a_query_log(
    question: str = "¿Qué es el habeas corpus?",
    answer: str = "El habeas corpus es un derecho fundamental.",
    sources: list[Source] | None = None,
    out_of_scope: bool = False,
) -> QueryLog:
    return QueryLog(
        question=question,
        answer=answer,
        sources=sources if sources is not None else [a_source()],
        top_score=0.85,
        detected_area=None,
        out_of_scope=out_of_scope,
        share_token=_SHARE_TOKEN,
    )


@pytest.fixture
def query_log_finder() -> QueryLogFinder:
    return create_autospec(QueryLogFinder, spec_set=True, instance=True)


@pytest.fixture
def use_case(query_log_finder) -> GetSharedQueryUseCase:
    return GetSharedQueryUseCase(finder=query_log_finder)


class TestExecute:
    def test_returns_the_query_log_when_found(self, use_case, query_log_finder):
        query_log_finder.find_by_share_token.return_value = a_query_log()

        result = use_case.execute(_SHARE_TOKEN)

        assert result == a_query_log()

    def test_looks_up_by_the_given_share_token(self, use_case, query_log_finder):
        query_log_finder.find_by_share_token.return_value = a_query_log()

        use_case.execute(_SHARE_TOKEN)

        query_log_finder.find_by_share_token.assert_called_once_with(_SHARE_TOKEN)

    def test_does_not_touch_the_rag_pipeline(self, use_case, query_log_finder):
        """No hay ningún embedder/vector store/LLM inyectado en este use case:
        estructuralmente no puede volver a llamar al RAG."""
        query_log_finder.find_by_share_token.return_value = a_query_log()

        use_case.execute(_SHARE_TOKEN)

        assert not hasattr(use_case, "_embedder")
        assert not hasattr(use_case, "_llm")

    def test_returns_none_when_not_found(self, use_case, query_log_finder):
        query_log_finder.find_by_share_token.return_value = None

        assert use_case.execute("no-existe") is None

    def test_propagates_finder_errors(self, use_case, query_log_finder):
        query_log_finder.find_by_share_token.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError):
            use_case.execute(_SHARE_TOKEN)
