"""Integration tests for API endpoints using TestClient."""
from __future__ import annotations

import logging

import pytest
import requests
from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_settings, get_use_case
from backend.app.api.main import app
from backend.app.application.query_use_case import QueryUseCase
from backend.app.domain.entities import RetrievedChunk
from backend.app.infrastructure.config import Settings
from backend.tests.conftest import FakeEmbedder, FakeLLMClient, FakeVectorStore


class TimeoutLLMClient:
    def generate(self, prompt: str, system: str = "") -> str:
        raise requests.exceptions.Timeout("LLM timed out")


_CHUNK = RetrievedChunk(
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

_LOW_SCORE_CHUNK = RetrievedChunk(
    chunk_id="c2",
    text="Texto irrelevante.",
    score=0.30,
    source_type="constitucion",
    metadata={"article_numero": "1", "titulo": "Otro", "url_original": "http://example.com"},
)


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
def real_use_case() -> QueryUseCase:
    return QueryUseCase(
        embedder=FakeEmbedder(),
        store=FakeVectorStore(chunks=[_CHUNK]),
        llm=FakeLLMClient(answer="El habeas corpus es un derecho fundamental."),
    )


@pytest.fixture
def out_of_scope_use_case() -> QueryUseCase:
    return QueryUseCase(
        embedder=FakeEmbedder(),
        store=FakeVectorStore(chunks=[_LOW_SCORE_CHUNK]),
        llm=FakeLLMClient(),
    )


@pytest.fixture
def client(test_settings: Settings, real_use_case: QueryUseCase) -> TestClient:
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_use_case] = lambda: real_use_case
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def out_of_scope_client(test_settings: Settings, out_of_scope_use_case: QueryUseCase) -> TestClient:
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_use_case] = lambda: out_of_scope_use_case
    with TestClient(app) as c:
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

    def test_valid_question_returns_200(self, client: TestClient):
        response = client.post("/api/query", json={"question": "¿Qué es el habeas corpus?"})
        assert response.status_code == 200

    def test_response_contains_answer(self, client: TestClient):
        data = client.post("/api/query", json={"question": "¿Qué es el habeas corpus?"}).json()
        assert data["answer"] == "El habeas corpus es un derecho fundamental."

    def test_response_contains_sources(self, client: TestClient):
        data = client.post("/api/query", json={"question": "¿Qué es el habeas corpus?"}).json()
        assert len(data["sources"]) == 1
        assert data["sources"][0]["chunk_id"] == "c1"
        assert data["sources"][0]["source_type"] == "constitucion"

    def test_response_contains_processing_time(self, client: TestClient):
        data = client.post("/api/query", json={"question": "¿Qué es el habeas corpus?"}).json()
        assert data["processing_time_ms"] > 0

    def test_out_of_scope_returns_true(self, out_of_scope_client: TestClient):
        data = out_of_scope_client.post(
            "/api/query", json={"question": "¿Cuánto cuesta el arroz?"}
        ).json()
        assert data["out_of_scope"] is True
        assert data["sources"] == []

    def test_in_scope_out_of_scope_is_false(self, client: TestClient):
        data = client.post("/api/query", json={"question": "¿Qué es el habeas corpus?"}).json()
        assert data["out_of_scope"] is False


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


@pytest.fixture
def timeout_use_case() -> QueryUseCase:
    return QueryUseCase(
        embedder=FakeEmbedder(),
        store=FakeVectorStore(chunks=[_CHUNK]),
        llm=TimeoutLLMClient(),
    )


@pytest.fixture
def timeout_client(test_settings: Settings, timeout_use_case: QueryUseCase) -> TestClient:
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_use_case] = lambda: timeout_use_case
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


class TestTimeoutHandling:
    def test_timeout_returns_503(self, timeout_client: TestClient):
        response = timeout_client.post("/api/query", json={"question": "¿Qué es el habeas corpus?"})
        assert response.status_code == 503

    def test_timeout_response_has_detail(self, timeout_client: TestClient):
        data = timeout_client.post("/api/query", json={"question": "¿Qué es el habeas corpus?"}).json()
        assert "detail" in data


class TestInputValidation:
    def test_whitespace_only_question_returns_422(self, client: TestClient):
        assert client.post("/api/query", json={"question": "   "}).status_code == 422

    def test_question_is_stripped_before_processing(self, client: TestClient):
        response = client.post("/api/query", json={"question": "  ¿Qué es el habeas corpus?  "})
        assert response.status_code == 200


class TestRequestLogging:
    def test_query_is_logged(self, client: TestClient, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.INFO, logger="parcerolegal"):
            client.post("/api/query", json={"question": "¿Qué es el habeas corpus?"})
        assert any("query" in r.message.lower() for r in caplog.records)
