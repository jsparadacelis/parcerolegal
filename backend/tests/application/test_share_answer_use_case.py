"""Tests for ShareAnswerUseCase.execute() — publica una pregunta bajo un link."""
from __future__ import annotations

from unittest.mock import create_autospec

import pytest

from backend.app.application.query_use_case import QueryUseCase
from backend.app.application.share_answer_use_case import ShareAnswerUseCase
from backend.app.domain.entities import QueryResult, Source
from backend.app.domain.ports import SharedAnswerStore

_QUESTION = "¿Qué es el habeas corpus?"


def a_query_result(
    answer: str = "El habeas corpus es un derecho fundamental.",
    sources: list[Source] | None = None,
    out_of_scope: bool = False,
) -> QueryResult:
    return QueryResult(
        answer=answer,
        sources=sources if sources is not None else [a_source()],
        out_of_scope=out_of_scope,
        processing_time_ms=350.0,
    )


def a_source() -> Source:
    return Source(
        chunk_id="c1",
        source_type="constitucion",
        title="Art. 30",
        url="https://example.com/art30",
    )


@pytest.fixture
def query_use_case() -> QueryUseCase:
    return create_autospec(QueryUseCase, spec_set=True, instance=True)


@pytest.fixture
def shared_answer_store() -> SharedAnswerStore:
    return create_autospec(SharedAnswerStore, spec_set=True, instance=True)


@pytest.fixture
def use_case(query_use_case, shared_answer_store) -> ShareAnswerUseCase:
    return ShareAnswerUseCase(query_use_case=query_use_case, store=shared_answer_store)


class TestExecute:
    def test_runs_the_rag_pipeline_with_the_question(self, use_case, query_use_case):
        query_use_case.execute.return_value = a_query_result()

        use_case.execute(_QUESTION)

        query_use_case.execute.assert_called_once_with(_QUESTION)

    def test_returns_a_generated_share_id(self, use_case, query_use_case):
        query_use_case.execute.return_value = a_query_result()

        share_id = use_case.execute(_QUESTION)

        assert isinstance(share_id, str)
        assert len(share_id) > 0

    def test_generates_a_different_id_on_each_call(self, use_case, query_use_case):
        query_use_case.execute.return_value = a_query_result()

        first_id = use_case.execute(_QUESTION)
        second_id = use_case.execute(_QUESTION)

        assert first_id != second_id

    def test_saves_a_shared_answer_with_the_query_result(
        self, use_case, query_use_case, shared_answer_store
    ):
        query_use_case.execute.return_value = a_query_result(
            answer="respuesta", sources=[a_source()], out_of_scope=False
        )

        share_id = use_case.execute(_QUESTION)

        saved = shared_answer_store.save.call_args[0][0]
        assert saved.id == share_id
        assert saved.question == _QUESTION
        assert saved.answer == "respuesta"
        assert saved.sources == [a_source()]
        assert saved.out_of_scope is False

    def test_saves_out_of_scope_answers_too(self, use_case, query_use_case, shared_answer_store):
        query_use_case.execute.return_value = a_query_result(sources=[], out_of_scope=True)

        use_case.execute(_QUESTION)

        saved = shared_answer_store.save.call_args[0][0]
        assert saved.out_of_scope is True
        assert saved.sources == []

    def test_propagates_store_errors(self, use_case, query_use_case, shared_answer_store):
        query_use_case.execute.return_value = a_query_result()
        shared_answer_store.save.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError):
            use_case.execute(_QUESTION)
