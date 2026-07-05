"""Tests for QueryUseCase.execute() — full RAG pipeline."""
from __future__ import annotations

import pytest

from backend.app.application.query_use_case import QueryUseCase
from backend.app.domain.entities import QueryResult, RetrievedChunk
from backend.tests.conftest import FakeEmbedder, FakeLLMClient, FakeVectorStore

_CHUNK_ABOVE = RetrievedChunk(
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

_CHUNK_ABOVE_2 = RetrievedChunk(
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

_CHUNK_BELOW = RetrievedChunk(
    chunk_id="c2",
    text="Texto irrelevante.",
    score=0.30,
    source_type="constitucion",
    metadata={"article_numero": "1", "titulo": "Otro", "url_original": "http://example.com"},
)

_SENTENCIA_CHUNK = RetrievedChunk(
    chunk_id="c3",
    text="La sentencia T-760 protege la salud.",
    score=0.79,
    source_type="sentencia",
    metadata={"sentencia_id": "T-760-2008", "source_url": "http://corte.gov.co/T-760"},
)


@pytest.fixture
def use_case() -> QueryUseCase:
    return QueryUseCase(
        embedder=FakeEmbedder(),
        store=FakeVectorStore(chunks=[_CHUNK_ABOVE]),
        llm=FakeLLMClient(answer="El habeas corpus es un derecho fundamental."),
    )


@pytest.fixture
def out_of_scope_use_case() -> QueryUseCase:
    """Store vacío → siempre cae en la rama de fuera-de-alcance."""
    return QueryUseCase(
        embedder=FakeEmbedder(),
        store=FakeVectorStore(chunks=[]),
        llm=FakeLLMClient(),
    )


class TestQueryUseCaseExecute:
    def test_returns_query_result(self, use_case):
        result = use_case.execute("¿Qué es el habeas corpus?")
        assert isinstance(result, QueryResult)

    def test_answer_comes_from_llm(self, use_case):
        result = use_case.execute("¿Qué es el habeas corpus?")
        assert result.answer == "El habeas corpus es un derecho fundamental."

    def test_out_of_scope_false_when_chunks_pass_threshold(self, use_case):
        result = use_case.execute("¿Qué es el habeas corpus?")
        assert result.out_of_scope is False

    def test_processing_time_ms_is_positive(self, use_case):
        result = use_case.execute("¿Qué es el habeas corpus?")
        assert result.processing_time_ms > 0

    def test_sources_built_from_constitucion_chunk(self, use_case):
        result = use_case.execute("¿Qué es el habeas corpus?")
        assert len(result.sources) == 1
        source = result.sources[0]
        assert source.chunk_id == "c1"
        assert source.source_type == "constitucion"
        assert "30" in source.title
        assert source.url == "http://example.com/art30"

    def test_sources_built_from_sentencia_chunk(self):
        uc = QueryUseCase(
            embedder=FakeEmbedder(),
            store=FakeVectorStore(chunks=[_SENTENCIA_CHUNK]),
            llm=FakeLLMClient(),
        )
        result = uc.execute("¿Qué protege T-760?")
        source = result.sources[0]
        assert source.source_type == "sentencia"
        assert source.title == "T-760-2008"
        assert source.url == "http://corte.gov.co/T-760"

    def test_out_of_scope_when_all_chunks_below_threshold(self):
        uc = QueryUseCase(
            embedder=FakeEmbedder(),
            store=FakeVectorStore(chunks=[_CHUNK_BELOW]),
            llm=FakeLLMClient(),
        )
        result = uc.execute("¿Cuánto cuesta el arroz?")
        assert result.out_of_scope is True
        assert result.sources == []

    def test_out_of_scope_answer_mentions_detected_area(self, out_of_scope_use_case):
        result = out_of_scope_use_case.execute(
            "¿puedo quedarme con los bienes tras el divorcio?"
        )
        assert result.out_of_scope is True
        assert "Civil" in result.answer

    def test_out_of_scope_answer_is_generic_when_area_unknown(self, out_of_scope_use_case):
        result = out_of_scope_use_case.execute("cuánto cuesta un carro en Colombia")
        assert result.out_of_scope is True
        assert "corpus de Parcero Legal" in result.answer

    def test_out_of_scope_returns_empty_sources(self, out_of_scope_use_case):
        result = out_of_scope_use_case.execute("pregunta fuera de alcance")
        assert result.sources == []

    def test_out_of_scope_does_not_call_llm(self):
        calls: list[str] = []

        class TrackingLLM:
            def generate(self, prompt: str, system: str = "") -> str:
                calls.append(prompt)
                return "respuesta"

        uc = QueryUseCase(
            embedder=FakeEmbedder(),
            store=FakeVectorStore(chunks=[_CHUNK_BELOW]),
            llm=TrackingLLM(),
        )
        uc.execute("pregunta fuera de scope")
        assert calls == []

    def test_prompt_contains_question_and_chunk_text(self):
        calls: list[dict] = []

        class CapturingLLM:
            def generate(self, prompt: str, system: str = "") -> str:
                calls.append({"prompt": prompt, "system": system})
                return "respuesta"

        uc = QueryUseCase(
            embedder=FakeEmbedder(),
            store=FakeVectorStore(chunks=[_CHUNK_ABOVE]),
            llm=CapturingLLM(),
        )
        uc.execute("¿Qué es el habeas corpus?")
        assert "¿Qué es el habeas corpus?" in calls[0]["prompt"]
        assert "El habeas corpus protege la libertad personal." in calls[0]["prompt"]

    def test_llm_receives_non_empty_system_role(self):
        calls: list[dict] = []

        class CapturingLLM:
            def generate(self, prompt: str, system: str = "") -> str:
                calls.append({"prompt": prompt, "system": system})
                return "respuesta"

        uc = QueryUseCase(
            embedder=FakeEmbedder(),
            store=FakeVectorStore(chunks=[_CHUNK_ABOVE]),
            llm=CapturingLLM(),
        )
        uc.execute("¿Qué es el habeas corpus?")
        assert calls[0]["system"] != ""

    def test_system_role_instructs_citations(self):
        calls: list[dict] = []

        class CapturingLLM:
            def generate(self, prompt: str, system: str = "") -> str:
                calls.append({"prompt": prompt, "system": system})
                return "respuesta"

        uc = QueryUseCase(
            embedder=FakeEmbedder(),
            store=FakeVectorStore(chunks=[_CHUNK_ABOVE]),
            llm=CapturingLLM(),
        )
        uc.execute("¿Qué es el habeas corpus?")
        assert "[1]" in calls[0]["system"]

    def test_user_prompt_numbers_fragments(self):
        calls: list[dict] = []

        class CapturingLLM:
            def generate(self, prompt: str, system: str = "") -> str:
                calls.append({"prompt": prompt, "system": system})
                return "respuesta"

        uc = QueryUseCase(
            embedder=FakeEmbedder(),
            store=FakeVectorStore(chunks=[_CHUNK_ABOVE, _CHUNK_ABOVE_2]),
            llm=CapturingLLM(),
        )
        uc.execute("¿Qué es el habeas corpus?")
        assert "[1]" in calls[0]["prompt"]
        assert "[2]" in calls[0]["prompt"]

    def test_passes_extracted_sentencia_id_to_store(self):
        store = FakeVectorStore(chunks=[_SENTENCIA_CHUNK])
        uc = QueryUseCase(embedder=FakeEmbedder(), store=store, llm=FakeLLMClient())

        uc.execute("¿Qué dice la sentencia T-760 de 2008?")

        assert store.last_sentencia_id == "T-760-08"

    def test_sentencia_match_bypasses_similarity_threshold(self):
        low_score_but_matched = RetrievedChunk(
            chunk_id="c5",
            text="Texto de la sentencia T-760.",
            score=0.20,
            source_type="sentencia",
            metadata={"sentencia_id": "T-760-08", "source_url": "http://corte.gov.co/T-760"},
        )
        store = FakeVectorStore(chunks=[low_score_but_matched])
        uc = QueryUseCase(embedder=FakeEmbedder(), store=store, llm=FakeLLMClient())

        result = uc.execute("¿Qué dice la sentencia T-760 de 2008?")

        assert result.out_of_scope is False

    def test_passes_none_when_question_has_no_sentencia_reference(self):
        store = FakeVectorStore(chunks=[_CHUNK_ABOVE])
        uc = QueryUseCase(embedder=FakeEmbedder(), store=store, llm=FakeLLMClient())

        uc.execute("¿Qué es el habeas corpus?")

        assert store.last_sentencia_id is None

    def test_construction_stores_ports(self):
        uc = QueryUseCase(
            embedder=FakeEmbedder(),
            store=FakeVectorStore(),
            llm=FakeLLMClient(),
        )
        assert uc._embedder is not None
        assert uc._store is not None
        assert uc._llm is not None
