"""Tests for QueryUseCase.execute() — full RAG pipeline."""
from __future__ import annotations

from unittest.mock import create_autospec

import pytest

from backend.app.application.query_use_case import QueryUseCase
from backend.app.domain.entities import QueryResult, RetrievedChunk
from backend.app.domain.ports import Embedder, LLMClient, VectorStore
from backend.app.infrastructure.config import DEFAULT_TOP_K

_HABEAS_CORPUS_QUESTION = "¿Qué es el habeas corpus?"
_SENTENCIA_QUESTION = "¿Qué dice la sentencia T-760 de 2008?"


def a_relevant_constitucion_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c1",
        text="El habeas corpus protege la libertad personal.",
        score=0.82,
        source_type="constitucion",
        metadata={
            "article_numero": "30",
            "titulo": "Habeas Corpus",
            "url_original": "http://example.com/art30",
        },
    )


def another_relevant_constitucion_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c4",
        text="Toda persona tiene derecho a la libertad.",
        score=0.78,
        source_type="constitucion",
        metadata={
            "article_numero": "28",
            "titulo": "Libertad",
            "url_original": "http://example.com/art28",
        },
    )


def an_irrelevant_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c2",
        text="Texto irrelevante.",
        score=0.30,
        source_type="constitucion",
        metadata={"article_numero": "1", "titulo": "Otro", "url_original": "http://example.com"},
    )


def a_sentencia_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c3",
        text="La sentencia T-760 protege la salud.",
        score=0.79,
        source_type="sentencia",
        metadata={"sentencia_id": "T-760-2008", "source_url": "http://corte.gov.co/T-760"},
    )


def a_low_score_sentencia_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c5",
        text="Texto de la sentencia T-760.",
        score=0.20,
        source_type="sentencia",
        metadata={"sentencia_id": "T-760-08", "source_url": "http://corte.gov.co/T-760"},
    )


@pytest.fixture
def embedder() -> Embedder:
    return create_autospec(Embedder, spec_set=True, instance=True)


@pytest.fixture
def store() -> VectorStore:
    return create_autospec(VectorStore, spec_set=True, instance=True)


@pytest.fixture
def llm() -> LLMClient:
    return create_autospec(LLMClient, spec_set=True, instance=True)


@pytest.fixture
def use_case(embedder, store, llm) -> QueryUseCase:
    return QueryUseCase(embedder=embedder, store=store, llm=llm, top_k=DEFAULT_TOP_K)


class TestExecuteReturnsResult:
    def test_returns_query_result(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "El habeas corpus es un derecho fundamental."

        result = use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert isinstance(result, QueryResult)

    def test_answer_comes_from_llm(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "El habeas corpus es un derecho fundamental."

        result = use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert result.answer == "El habeas corpus es un derecho fundamental."

    def test_out_of_scope_false_when_chunks_pass_threshold(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert result.out_of_scope is False

    def test_processing_time_ms_is_positive(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert result.processing_time_ms > 0


class TestSourceMapping:
    def test_sources_built_from_constitucion_chunk(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert len(result.sources) == 1
        source = result.sources[0]
        assert source.chunk_id == "c1"
        assert source.source_type == "constitucion"
        assert "30" in source.title
        assert source.url == "http://example.com/art30"

    def test_sources_built_from_sentencia_chunk(self, use_case, store, llm):
        store.search.return_value = [a_sentencia_chunk()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute("¿Qué protege T-760?")

        source = result.sources[0]
        assert source.source_type == "sentencia"
        assert source.title == "T-760-2008"
        assert source.url == "http://corte.gov.co/T-760"


class TestOutOfScope:
    def test_out_of_scope_when_all_chunks_below_threshold(self, use_case, store):
        store.search.return_value = [an_irrelevant_chunk()]

        result = use_case.execute("¿Cuánto cuesta el arroz?")

        assert result.out_of_scope is True
        assert result.sources == []

    def test_out_of_scope_returns_empty_sources(self, use_case, store):
        store.search.return_value = []

        result = use_case.execute("pregunta fuera de alcance")

        assert result.sources == []

    def test_out_of_scope_does_not_call_llm(self, use_case, store, llm):
        store.search.return_value = [an_irrelevant_chunk()]

        use_case.execute("pregunta fuera de scope")

        llm.generate.assert_not_called()

    def test_out_of_scope_answer_mentions_detected_area(self, use_case, store):
        store.search.return_value = []

        result = use_case.execute("¿puedo quedarme con los bienes tras el divorcio?")

        assert result.out_of_scope is True
        assert "Civil" in result.answer

    def test_out_of_scope_answer_is_generic_when_area_unknown(self, use_case, store):
        store.search.return_value = []

        result = use_case.execute("cuánto cuesta un carro en Colombia")

        assert result.out_of_scope is True
        assert "corpus de Parcero Legal" in result.answer


class TestPromptConstruction:
    def test_prompt_contains_question_and_chunk_text(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "respuesta"

        use_case.execute(_HABEAS_CORPUS_QUESTION)

        prompt = llm.generate.call_args.args[0]
        assert _HABEAS_CORPUS_QUESTION in prompt
        assert "El habeas corpus protege la libertad personal." in prompt

    def test_llm_receives_non_empty_system_role(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "respuesta"

        use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert llm.generate.call_args.kwargs["system"] != ""

    def test_system_role_instructs_citations(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "respuesta"

        use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert "[1]" in llm.generate.call_args.kwargs["system"]

    def test_user_prompt_numbers_fragments(self, use_case, store, llm):
        store.search.return_value = [
            a_relevant_constitucion_chunk(),
            another_relevant_constitucion_chunk(),
        ]
        llm.generate.return_value = "respuesta"

        use_case.execute(_HABEAS_CORPUS_QUESTION)

        prompt = llm.generate.call_args.args[0]
        assert "[1]" in prompt
        assert "[2]" in prompt


class TestSentenciaReference:
    def test_passes_extracted_sentencia_id_to_store(self, use_case, store, llm):
        store.search.return_value = [a_sentencia_chunk()]
        llm.generate.return_value = "respuesta"

        use_case.execute(_SENTENCIA_QUESTION)

        assert store.search.call_args.kwargs["sentencia_id"] == "T-760-08"

    def test_sentencia_match_bypasses_similarity_threshold(self, use_case, store, llm):
        store.search.return_value = [a_low_score_sentencia_chunk()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute(_SENTENCIA_QUESTION)

        assert result.out_of_scope is False

    def test_passes_none_when_question_has_no_sentencia_reference(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "respuesta"

        use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert store.search.call_args.kwargs["sentencia_id"] is None


class TestConstruction:
    def test_construction_stores_ports(self, use_case, embedder, store, llm):
        assert use_case._embedder is embedder
        assert use_case._store is store
        assert use_case._llm is llm
