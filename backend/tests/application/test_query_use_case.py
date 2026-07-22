"""Tests for QueryUseCase.execute() — full RAG pipeline."""
from __future__ import annotations

import logging
from unittest.mock import create_autospec

import pytest

from backend.app.application.query_use_case import QueryUseCase
from backend.app.domain.entities import MissedQuery, QueryResult, RetrievedChunk
from backend.app.domain.ports import (
    Embedder,
    LLMClient,
    MissedQueryStore,
    VectorStore,
)
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


def a_codigo_penal_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c7",
        text="El que se apodere de una cosa mueble ajena incurrirá en prisión.",
        score=0.77,
        source_type="codigo_penal",
        metadata={
            "article_numero": 239,
            "sufijo": None,
            "nombre": "Hurto",
            "url_original": "http://example.com/codigo_penal#239",
        },
    )


def a_codigo_penal_chunk_with_sufijo() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c8",
        text="Quien causare la muerte a una mujer por su condición de ser mujer.",
        score=0.81,
        source_type="codigo_penal",
        metadata={
            "article_numero": 104,
            "sufijo": "A",
            "nombre": "Feminicidio",
            "url_original": "http://example.com/codigo_penal#104A",
        },
    )


def a_codigo_penal_chunk_without_nombre() -> RetrievedChunk:
    """Simula uno de los ~50/480 artículos donde 'nombre' quedó vacío en el
    scraper (ver .aiplans/scrape-codigo-penal) — el título debe degradar con
    gracia, sin guion colgante ni 'None' visible."""
    return RetrievedChunk(
        chunk_id="c9",
        text="Artículo derogado por el artículo 56 de la Ley 1762 de 2015.",
        score=0.75,
        source_type="codigo_penal",
        metadata={
            "article_numero": 447,
            "sufijo": "A",
            "nombre": "",
            "url_original": "http://example.com/codigo_penal#447A",
        },
    )


def a_sentencia_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c3",
        text="La sentencia T-760 protege la salud.",
        score=0.79,
        source_type="sentencia",
        metadata={"sentencia_id": "T-760-2008", "source_url": "http://corte.gov.co/T-760"},
    )


def another_chunk_of_same_sentencia() -> RetrievedChunk:
    """Otro fragmento de la MISMA sentencia que a_sentencia_chunk (mismo id/url)."""
    return RetrievedChunk(
        chunk_id="c6",
        text="Otro considerando de la sentencia T-760.",
        score=0.71,
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
def missed_query_store() -> MissedQueryStore:
    return create_autospec(MissedQueryStore, spec_set=True, instance=True)


@pytest.fixture
def use_case(embedder, store, llm, missed_query_store) -> QueryUseCase:
    return QueryUseCase(
        embedder=embedder,
        store=store,
        llm=llm,
        top_k=DEFAULT_TOP_K,
        missed_query_store=missed_query_store,
    )


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

    def test_sources_built_from_codigo_penal_chunk(self, use_case, store, llm):
        store.search.return_value = [a_codigo_penal_chunk()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute("¿qué pena tiene el hurto?")

        source = result.sources[0]
        assert source.source_type == "codigo_penal"
        assert source.title == "Art. 239 CP — Hurto"
        assert source.url == "http://example.com/codigo_penal#239"

    def test_codigo_penal_source_title_includes_sufijo(self, use_case, store, llm):
        store.search.return_value = [a_codigo_penal_chunk_with_sufijo()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute("¿qué es el feminicidio?")

        assert result.sources[0].title == "Art. 104A CP — Feminicidio"

    def test_codigo_penal_source_title_degrades_without_nombre(self, use_case, store, llm):
        store.search.return_value = [a_codigo_penal_chunk_without_nombre()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute("¿qué dice el artículo 447A?")

        title = result.sources[0].title
        assert title == "Art. 447A CP"
        assert "None" not in title
        assert not title.endswith("—")


class TestSourceDeduplication:
    def test_repeated_document_appears_once_in_sources(self, use_case, store, llm):
        store.search.return_value = [
            a_sentencia_chunk(),
            another_chunk_of_same_sentencia(),
        ]
        llm.generate.return_value = "respuesta"

        result = use_case.execute("¿Qué protege T-760?")

        assert len(result.sources) == 1
        assert result.sources[0].title == "T-760-2008"

    def test_distinct_documents_are_all_kept(self, use_case, store, llm):
        store.search.return_value = [
            a_sentencia_chunk(),
            a_relevant_constitucion_chunk(),
        ]
        llm.generate.return_value = "respuesta"

        result = use_case.execute("¿Qué protege T-760?")

        assert len(result.sources) == 2

    def test_all_fragments_still_reach_the_llm(self, use_case, store, llm):
        store.search.return_value = [
            a_sentencia_chunk(),
            another_chunk_of_same_sentencia(),
        ]
        llm.generate.return_value = "respuesta"

        use_case.execute("¿Qué protege T-760?")

        prompt = llm.generate.call_args.args[0]
        assert "La sentencia T-760 protege la salud." in prompt
        assert "Otro considerando de la sentencia T-760." in prompt


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

    def test_system_role_states_total_fragment_count(self, use_case, store, llm):
        store.search.return_value = [
            a_relevant_constitucion_chunk(),
            another_relevant_constitucion_chunk(),
        ]
        llm.generate.return_value = "respuesta"

        use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert "[1] a [2]" in llm.generate.call_args.kwargs["system"]

    def test_system_role_prohibits_citations_outside_range(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "respuesta"

        use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert "prohibido" in llm.generate.call_args.kwargs["system"].lower()

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


class TestCitationSanitization:
    def test_removes_hallucinated_citation_from_answer(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "Igualdad [1], [13]"

        result = use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert result.answer == "Igualdad [1]"

    def test_keeps_valid_citations_when_no_hallucination(self, use_case, store, llm):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "El habeas corpus protege [1] la libertad."

        result = use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert result.answer == "El habeas corpus protege [1] la libertad."

    def test_multiple_hallucinated_citations_all_removed(self, use_case, store, llm):
        store.search.return_value = [
            a_relevant_constitucion_chunk(),
            another_relevant_constitucion_chunk(),
        ]
        llm.generate.return_value = "* Igualdad [1], [13]\n* Paz [1], [22]"

        result = use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert result.answer == "* Igualdad [1]\n* Paz [1]"

    def test_logs_warning_when_hallucinated_citation_detected(
        self, use_case, store, llm, caplog: pytest.LogCaptureFixture
    ):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "Igualdad [1], [13]"

        with caplog.at_level(logging.WARNING, logger="parcerolegal"):
            use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert any(r.levelname == "WARNING" for r in caplog.records)

    def test_does_not_log_warning_when_citations_valid(
        self, use_case, store, llm, caplog: pytest.LogCaptureFixture
    ):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "respuesta [1]"

        with caplog.at_level(logging.WARNING, logger="parcerolegal"):
            use_case.execute(_HABEAS_CORPUS_QUESTION)

        assert not any(r.levelname == "WARNING" for r in caplog.records)


class TestNarrowSourceCaveat:
    """Caso reportado 2026-07-22: 'Me pueden despedir sin justa causa' devolvía la
    doctrina de fuero de maternidad (SU-070-13) como si fuera la regla general de
    despido, sin aclarar que el corpus no cubre derecho laboral general y que la
    respuesta vino de un único caso puntual. Ver .aiplans/narrow-single-document-caveat.
    """

    _LABOR_QUESTION = "¿Me pueden despedir sin justa causa?"

    def test_adds_caveat_when_single_document_matches_excluded_area(self, use_case, store, llm):
        store.search.return_value = [a_sentencia_chunk(), another_chunk_of_same_sentencia()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute(self._LABOR_QUESTION)

        assert "T-760-2008" in result.answer
        assert "laboral" in result.answer.lower()

    def test_no_caveat_when_sources_are_diverse(self, use_case, store, llm):
        store.search.return_value = [a_sentencia_chunk(), a_relevant_constitucion_chunk()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute(self._LABOR_QUESTION)

        assert result.answer == "respuesta"

    def test_no_caveat_when_only_one_chunk_retrieved(self, use_case, store, llm):
        store.search.return_value = [a_sentencia_chunk()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute(self._LABOR_QUESTION)

        assert result.answer == "respuesta"

    def test_no_caveat_when_question_matches_no_excluded_area(self, use_case, store, llm):
        store.search.return_value = [a_sentencia_chunk(), another_chunk_of_same_sentencia()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute("¿Qué protege la sentencia sobre la salud?")

        assert result.answer == "respuesta"

    def test_no_caveat_when_user_explicitly_asked_for_that_sentencia(self, use_case, store, llm):
        store.search.return_value = [a_sentencia_chunk(), another_chunk_of_same_sentencia()]
        llm.generate.return_value = "respuesta"

        result = use_case.execute(_SENTENCIA_QUESTION)

        assert result.answer == "respuesta"


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


class TestQueryPersistence:
    def test_saves_record_when_out_of_scope(self, use_case, store, missed_query_store):
        store.search.return_value = [an_irrelevant_chunk()]

        use_case.execute("¿Cuánto cuesta el arroz?")

        missed_query_store.save.assert_called_once()
        saved = missed_query_store.save.call_args.args[0]
        assert saved.out_of_scope is True

    def test_saves_record_when_in_scope(self, use_case, store, llm, missed_query_store):
        store.search.return_value = [a_relevant_constitucion_chunk()]
        llm.generate.return_value = "respuesta"

        use_case.execute(_HABEAS_CORPUS_QUESTION)

        missed_query_store.save.assert_called_once()
        saved = missed_query_store.save.call_args.args[0]
        assert saved.out_of_scope is False

    def test_saved_record_carries_question_and_answer(self, use_case, store, missed_query_store):
        store.search.return_value = []

        result = use_case.execute("pregunta fuera de alcance")

        saved = missed_query_store.save.call_args.args[0]
        assert isinstance(saved, MissedQuery)
        assert saved.question == "pregunta fuera de alcance"
        assert saved.answer == result.answer

    def test_saved_record_carries_top_score_of_retrieved_chunks(
        self, use_case, store, missed_query_store
    ):
        store.search.return_value = [an_irrelevant_chunk()]

        use_case.execute("¿Cuánto cuesta el arroz?")

        saved = missed_query_store.save.call_args.args[0]
        assert saved.top_score == 0.30

    def test_saved_record_top_score_is_none_when_no_chunks(
        self, use_case, store, missed_query_store
    ):
        store.search.return_value = []

        use_case.execute("pregunta fuera de alcance")

        saved = missed_query_store.save.call_args.args[0]
        assert saved.top_score is None

    def test_saved_record_carries_detected_area(self, use_case, store, missed_query_store):
        store.search.return_value = []

        use_case.execute("¿puedo quedarme con los bienes tras el divorcio?")

        saved = missed_query_store.save.call_args.args[0]
        assert saved.detected_area is not None
        assert "Civil" in saved.detected_area

    def test_persistence_failure_does_not_break_response(
        self, use_case, store, missed_query_store
    ):
        store.search.return_value = [an_irrelevant_chunk()]
        missed_query_store.save.side_effect = RuntimeError("supabase caído")

        result = use_case.execute("¿Cuánto cuesta el arroz?")

        assert result.out_of_scope is True

    def test_works_without_a_missed_query_store(self, embedder, store, llm):
        store.search.return_value = []
        use_case = QueryUseCase(embedder=embedder, store=store, llm=llm, top_k=DEFAULT_TOP_K)

        result = use_case.execute("pregunta fuera de alcance")

        assert result.out_of_scope is True


class TestConstruction:
    def test_construction_stores_ports(self, use_case, embedder, store, llm):
        assert use_case._embedder is embedder
        assert use_case._store is store
        assert use_case._llm is llm

    def test_construction_stores_missed_query_store(self, use_case, missed_query_store):
        assert use_case._missed_query_store is missed_query_store
