"""Integration tests for API endpoints using TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_settings, get_use_case
from backend.app.api.main import app
from backend.app.application.query_use_case import QueryUseCase
from backend.app.infrastructure.config import Settings
from backend.tests.conftest import FakeEmbedder, FakeLLMClient, FakeVectorStore


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
def stub_use_case() -> QueryUseCase:
    return QueryUseCase(
        embedder=FakeEmbedder(),
        store=FakeVectorStore(),
        llm=FakeLLMClient(),
    )


@pytest.fixture
def client(test_settings: Settings, stub_use_case: QueryUseCase) -> TestClient:
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_use_case] = lambda: stub_use_case
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_returns_200(self, client: TestClient):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_response_structure(self, client: TestClient):
        data = client.get("/api/health").json()
        assert data["status"] == "ok"
        assert "environment" in data

    def test_shows_test_environment(self, client: TestClient):
        data = client.get("/api/health").json()
        assert data["environment"] == "testing"


class TestQueryEndpoint:
    def test_empty_body_returns_422(self, client: TestClient):
        response = client.post("/api/query", json={})
        assert response.status_code == 422

    def test_short_question_returns_422(self, client: TestClient):
        response = client.post("/api/query", json={"question": "ab"})
        assert response.status_code == 422

    def test_valid_question_raises_not_implemented(self, stub_use_case: QueryUseCase):
        """Use case stub raises NotImplementedError until RAG is implemented."""
        import pytest

        with pytest.raises(NotImplementedError, match="RAG pipeline"):
            stub_use_case.execute("¿Qué dice el artículo 13?")


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
