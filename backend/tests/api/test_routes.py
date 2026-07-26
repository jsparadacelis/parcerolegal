"""Integration tests for API endpoints using TestClient."""
from __future__ import annotations

import json
import logging
from unittest.mock import create_autospec

import pytest
import requests
import responses
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.api.dependencies import (
    get_settings,
    get_share_use_case,
    get_shared_answer_finder,
    get_shared_answer_store,
    get_use_case,
)
from backend.app.api.main import app
from backend.app.application.query_use_case import QueryUseCase
from backend.app.application.share_answer_use_case import ShareAnswerUseCase
from backend.app.domain.entities import RetrievedChunk, SharedAnswer, Source
from backend.app.domain.ports import (
    Embedder,
    LLMClient,
    SharedAnswerFinder,
    SharedAnswerStore,
    VectorStore,
)
from backend.app.infrastructure.config import DEFAULT_TOP_K, Settings
from backend.app.infrastructure.supabase_query_log_store import (
    SupabaseQueryLogStore,
)

_QUESTION = "¿Qué es el habeas corpus?"
_ANSWER = "El habeas corpus es un derecho fundamental."
_SUPABASE_URL = "https://proj.supabase.co"
_SUPABASE_INSERT_URL = f"{_SUPABASE_URL}/rest/v1/queries"


def a_relevant_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c1",
        text="El habeas corpus protege la libertad.",
        score=0.85,
        source_type="constitucion",
        metadata={
            "article_numero": "30",
            "titulo": "Habeas Corpus",
            "url_original": "http://example.com/art30",
        },
    )


def a_relevant_chunk_as_source() -> Source:
    return Source(
        chunk_id="c1",
        source_type="constitucion",
        title="Art. 30 — Habeas Corpus",
        url="http://example.com/art30",
    )


def a_low_score_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c2",
        text="Texto irrelevante.",
        score=0.30,
        source_type="constitucion",
        metadata={"article_numero": "1", "titulo": "Otro", "url_original": "http://example.com"},
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
def query_log_store() -> SupabaseQueryLogStore:
    return SupabaseQueryLogStore(url=_SUPABASE_URL, api_key="test-key")


@pytest.fixture(autouse=True)
def mock_http():
    """Toda consulta se persiste ahora, así que ninguna llamada debe llegar a la red real."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as r:
        r.add(responses.POST, _SUPABASE_INSERT_URL, status=201)
        yield r


@pytest.fixture
def use_case(embedder, store, llm, query_log_store) -> QueryUseCase:
    return QueryUseCase(
        embedder=embedder,
        store=store,
        llm=llm,
        top_k=DEFAULT_TOP_K,
        query_log_store=query_log_store,
    )


@pytest.fixture
def shared_answer_store() -> SharedAnswerStore:
    return create_autospec(SharedAnswerStore, spec_set=True, instance=True)


@pytest.fixture
def shared_answer_finder() -> SharedAnswerFinder:
    return create_autospec(SharedAnswerFinder, spec_set=True, instance=True)


@pytest.fixture
def share_use_case(use_case, shared_answer_store) -> ShareAnswerUseCase:
    return ShareAnswerUseCase(query_use_case=use_case, store=shared_answer_store)


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        _env_file=None,
        groq_api_key="test-key",
        qdrant_url="http://localhost:6333",
        qdrant_api_key="test-key",
        environment="testing",
    )


@pytest.fixture
def client(
    test_settings: Settings,
    use_case: QueryUseCase,
    share_use_case: ShareAnswerUseCase,
    shared_answer_store: SharedAnswerStore,
    shared_answer_finder: SharedAnswerFinder,
) -> TestClient:
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_use_case] = lambda: use_case
    app.dependency_overrides[get_share_use_case] = lambda: share_use_case
    app.dependency_overrides[get_shared_answer_store] = lambda: shared_answer_store
    app.dependency_overrides[get_shared_answer_finder] = lambda: shared_answer_finder
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def unconfigured_share_client(test_settings: Settings, use_case: QueryUseCase) -> TestClient:
    """Simula Supabase sin configurar: las dependencias de compartir levantan 503."""

    def _raise_unconfigured():
        raise HTTPException(status_code=503, detail="Compartir no está disponible en este momento.")

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_use_case] = lambda: use_case
    app.dependency_overrides[get_share_use_case] = _raise_unconfigured
    app.dependency_overrides[get_shared_answer_store] = _raise_unconfigured
    app.dependency_overrides[get_shared_answer_finder] = _raise_unconfigured
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def lenient_client(test_settings: Settings, use_case: QueryUseCase) -> TestClient:
    """Client that surfaces server exceptions as responses (for exception handlers)."""
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_use_case] = lambda: use_case
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_returns_200(self, client: TestClient):
        assert client.get("/api/health").status_code == 200

    def test_response_structure(self, client: TestClient):
        data = client.get("/api/health").json()

        assert data["status"] == "ok"
        assert "environment" in data

    def test_shows_test_environment(self, client: TestClient):
        assert client.get("/api/health").json()["environment"] == "testing"


class TestQueryEndpoint:
    def test_empty_body_returns_422(self, client: TestClient):
        assert client.post("/api/query", json={}).status_code == 422

    def test_short_question_returns_422(self, client: TestClient):
        assert client.post("/api/query", json={"question": "ab"}).status_code == 422

    def test_valid_question_returns_200(self, client: TestClient, store, llm):
        store.search.return_value = [a_relevant_chunk()]
        llm.generate.return_value = _ANSWER

        response = client.post("/api/query", json={"question": _QUESTION})

        assert response.status_code == 200

    def test_response_contains_answer(self, client: TestClient, store, llm):
        store.search.return_value = [a_relevant_chunk()]
        llm.generate.return_value = _ANSWER

        data = client.post("/api/query", json={"question": _QUESTION}).json()

        assert data["answer"] == _ANSWER

    def test_response_contains_sources(self, client: TestClient, store, llm):
        store.search.return_value = [a_relevant_chunk()]
        llm.generate.return_value = _ANSWER

        data = client.post("/api/query", json={"question": _QUESTION}).json()

        assert len(data["sources"]) == 1
        assert data["sources"][0]["chunk_id"] == "c1"
        assert data["sources"][0]["source_type"] == "constitucion"

    def test_response_contains_processing_time(self, client: TestClient, store, llm):
        store.search.return_value = [a_relevant_chunk()]
        llm.generate.return_value = _ANSWER

        data = client.post("/api/query", json={"question": _QUESTION}).json()

        assert data["processing_time_ms"] > 0

    def test_out_of_scope_returns_true(self, client: TestClient, store, mock_http):
        store.search.return_value = [a_low_score_chunk()]

        response = client.post("/api/query", json={"question": "¿Cuánto cuesta el arroz?"})
        data = response.json()

        assert data["out_of_scope"] is True
        assert data["sources"] == []
        # fire-and-forget: la pregunta fuera de alcance se manda al cliente Supabase
        # sin afectar la respuesta al usuario (200 + out_of_scope).
        assert response.status_code == 200
        assert mock_http.calls[0].request.url == _SUPABASE_INSERT_URL
        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["question"] == "¿Cuánto cuesta el arroz?"
        assert sent["out_of_scope"] is True

    def test_in_scope_out_of_scope_is_false(self, client: TestClient, store, llm, mock_http):
        store.search.return_value = [a_relevant_chunk()]
        llm.generate.return_value = _ANSWER

        data = client.post("/api/query", json={"question": _QUESTION}).json()

        assert data["out_of_scope"] is False
        # las respuestas en alcance también se persisten ahora, no solo las que
        # caían bajo el umbral.
        assert mock_http.calls[0].request.url == _SUPABASE_INSERT_URL
        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["out_of_scope"] is False
        assert sent["sources"] == data["sources"]


class TestCORS:
    def test_cors_allows_origin(self, client: TestClient):
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.headers.get("access-control-allow-origin") == "*"


class TestTimeoutHandling:
    def test_timeout_returns_503(self, lenient_client: TestClient, store, llm):
        store.search.return_value = [a_relevant_chunk()]
        llm.generate.side_effect = requests.exceptions.Timeout("LLM timed out")

        response = lenient_client.post("/api/query", json={"question": _QUESTION})

        assert response.status_code == 503

    def test_timeout_response_has_detail(self, lenient_client: TestClient, store, llm):
        store.search.return_value = [a_relevant_chunk()]
        llm.generate.side_effect = requests.exceptions.Timeout("LLM timed out")

        data = lenient_client.post("/api/query", json={"question": _QUESTION}).json()

        assert "detail" in data


class TestInputValidation:
    def test_whitespace_only_question_returns_422(self, client: TestClient):
        assert client.post("/api/query", json={"question": "   "}).status_code == 422

    def test_question_is_stripped_before_processing(self, client: TestClient, store, llm):
        store.search.return_value = [a_relevant_chunk()]
        llm.generate.return_value = _ANSWER

        response = client.post("/api/query", json={"question": f"  {_QUESTION}  "})

        assert response.status_code == 200


class TestRequestLogging:
    def test_query_is_logged(self, client: TestClient, store, llm, caplog: pytest.LogCaptureFixture):
        store.search.return_value = [a_relevant_chunk()]
        llm.generate.return_value = _ANSWER

        with caplog.at_level(logging.INFO, logger="parcerolegal"):
            client.post("/api/query", json={"question": _QUESTION})

        assert any("query" in r.message.lower() for r in caplog.records)


class TestCreateShareEndpoint:
    def test_valid_question_returns_201_with_id(self, client: TestClient, store, llm):
        store.search.return_value = [a_relevant_chunk()]
        llm.generate.return_value = _ANSWER

        response = client.post("/api/shares", json={"question": _QUESTION})

        assert response.status_code == 201
        assert "id" in response.json()

    def test_persists_a_shared_answer_matching_the_regenerated_result(
        self, client: TestClient, store, llm, shared_answer_store
    ):
        store.search.return_value = [a_relevant_chunk()]
        llm.generate.return_value = _ANSWER

        response = client.post("/api/shares", json={"question": _QUESTION})

        share_id = response.json()["id"]
        saved = shared_answer_store.save.call_args[0][0]
        assert saved.id == share_id
        assert saved.question == _QUESTION
        assert saved.answer == _ANSWER
        assert saved.out_of_scope is False

    def test_empty_body_returns_422(self, client: TestClient):
        assert client.post("/api/shares", json={}).status_code == 422

    def test_returns_503_when_supabase_not_configured(self, unconfigured_share_client: TestClient):
        response = unconfigured_share_client.post("/api/shares", json={"question": _QUESTION})

        assert response.status_code == 503


class TestGetShareEndpoint:
    def test_returns_200_with_stored_content(self, client: TestClient, shared_answer_finder):
        shared_answer_finder.get.return_value = SharedAnswer(
            id="abc123",
            question=_QUESTION,
            answer=_ANSWER,
            sources=[a_relevant_chunk_as_source()],
            out_of_scope=False,
        )

        response = client.get("/api/shares/abc123")
        data = response.json()

        assert response.status_code == 200
        assert data["question"] == _QUESTION
        assert data["answer"] == _ANSWER
        assert data["sources"][0]["chunk_id"] == "c1"
        assert data["out_of_scope"] is False

    def test_returns_404_when_share_not_found(self, client: TestClient, shared_answer_finder):
        shared_answer_finder.get.return_value = None

        response = client.get("/api/shares/no-existe")

        assert response.status_code == 404

    def test_returns_503_when_supabase_not_configured(self, unconfigured_share_client: TestClient):
        response = unconfigured_share_client.get("/api/shares/abc123")

        assert response.status_code == 503
