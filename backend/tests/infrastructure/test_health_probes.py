"""Tests for the deep health check probes (infrastructure adapters).

Corte a nivel HTTP con `responses`, igual que el resto de adapters. Cada probe
lanza DependencyCheckError con un mensaje seguro de exponer (sin URLs ni
credenciales) cuando la dependencia responde pero no está sana.
"""

from __future__ import annotations

import json

import pytest
import requests
import responses

from backend.app.domain.ports import DependencyCheckError
from backend.app.infrastructure.config import (
    GROQ_MODELS_URL,
    HEALTH_CHECK_TIMEOUT_SECONDS,
    JINA_EMBEDDINGS_URL,
)
from backend.app.infrastructure.health_probes import (
    GroqProbe,
    JinaProbe,
    QdrantProbe,
    SupabaseProbe,
)

_API_KEY = "test-key"
_QDRANT_URL = "https://cluster.cloud.qdrant.io"
_COLLECTION = "parcerolegal"
_COLLECTION_URL = f"{_QDRANT_URL}/collections/{_COLLECTION}"
_LLM_MODEL = "openai/gpt-oss-120b"
_SUPABASE_URL = "https://proj.supabase.co"
_SUPABASE_TABLE_URL = f"{_SUPABASE_URL}/rest/v1/queries"


def a_collection_info(points_count: int | None = 1234, status: str = "green") -> dict:
    return {"result": {"status": status, "points_count": points_count}, "status": "ok"}


def a_models_listing(*model_ids: str) -> dict:
    return {"object": "list", "data": [{"id": model_id, "object": "model"} for model_id in model_ids]}


@pytest.fixture
def mock_http():
    with responses.RequestsMock() as r:
        yield r


@pytest.fixture
def qdrant_probe() -> QdrantProbe:
    return QdrantProbe(url=_QDRANT_URL, api_key=_API_KEY, collection=_COLLECTION)


@pytest.fixture
def jina_probe() -> JinaProbe:
    return JinaProbe(api_key=_API_KEY, model="jina-embeddings-v3", dimensions=1024)


@pytest.fixture
def groq_probe() -> GroqProbe:
    return GroqProbe(api_key=_API_KEY, model=_LLM_MODEL)


@pytest.fixture
def supabase_probe() -> SupabaseProbe:
    return SupabaseProbe(url=_SUPABASE_URL, api_key=_API_KEY, table="queries")


class TestQdrantProbe:
    def test_passes_when_collection_has_points(self, qdrant_probe, mock_http):
        mock_http.add(responses.GET, _COLLECTION_URL, json=a_collection_info())

        qdrant_probe.check()

    def test_sends_api_key_and_short_timeout(self, qdrant_probe, mock_http):
        mock_http.add(responses.GET, _COLLECTION_URL, json=a_collection_info())

        qdrant_probe.check()

        request = mock_http.calls[0].request
        assert request.headers["api-key"] == _API_KEY
        assert request.req_kwargs["timeout"] == HEALTH_CHECK_TIMEOUT_SECONDS

    @pytest.mark.parametrize("points_count", [0, None])
    def test_fails_when_collection_is_empty(self, qdrant_probe, mock_http, points_count):
        mock_http.add(responses.GET, _COLLECTION_URL, json=a_collection_info(points_count=points_count))

        with pytest.raises(DependencyCheckError, match="no tiene puntos"):
            qdrant_probe.check()

    def test_fails_when_collection_status_is_red(self, qdrant_probe, mock_http):
        mock_http.add(responses.GET, _COLLECTION_URL, json=a_collection_info(status="red"))

        with pytest.raises(DependencyCheckError, match="red"):
            qdrant_probe.check()

    def test_fails_when_collection_does_not_exist(self, qdrant_probe, mock_http):
        mock_http.add(responses.GET, _COLLECTION_URL, status=404)

        with pytest.raises(DependencyCheckError, match="HTTP 404"):
            qdrant_probe.check()

    def test_http_error_message_does_not_leak_the_url(self, qdrant_probe, mock_http):
        mock_http.add(responses.GET, _COLLECTION_URL, status=403)

        with pytest.raises(DependencyCheckError) as error:
            qdrant_probe.check()

        assert _QDRANT_URL not in str(error.value)

    def test_propagates_timeouts(self, qdrant_probe, mock_http):
        mock_http.add(responses.GET, _COLLECTION_URL, body=requests.exceptions.ReadTimeout())

        with pytest.raises(requests.exceptions.ReadTimeout):
            qdrant_probe.check()


class TestJinaProbe:
    def test_passes_when_embedding_is_returned(self, jina_probe, mock_http):
        mock_http.add(responses.POST, JINA_EMBEDDINGS_URL, json={"data": [{"embedding": [0.1] * 1024}]})

        jina_probe.check()

    def test_embeds_a_minimal_input_with_short_timeout(self, jina_probe, mock_http):
        mock_http.add(responses.POST, JINA_EMBEDDINGS_URL, json={"data": [{"embedding": [0.1] * 1024}]})

        jina_probe.check()

        request = mock_http.calls[0].request
        sent = json.loads(request.body)
        assert sent["model"] == "jina-embeddings-v3"
        assert sent["input"] == ["ping"]
        assert request.headers["Authorization"] == f"Bearer {_API_KEY}"
        assert request.req_kwargs["timeout"] == HEALTH_CHECK_TIMEOUT_SECONDS

    def test_fails_when_embedding_is_empty(self, jina_probe, mock_http):
        mock_http.add(responses.POST, JINA_EMBEDDINGS_URL, json={"data": [{"embedding": []}]})

        with pytest.raises(DependencyCheckError, match="vacío"):
            jina_probe.check()

    def test_fails_on_http_error(self, jina_probe, mock_http):
        mock_http.add(responses.POST, JINA_EMBEDDINGS_URL, status=401)

        with pytest.raises(DependencyCheckError, match="HTTP 401"):
            jina_probe.check()


class TestGroqProbe:
    def test_passes_when_configured_model_is_listed(self, groq_probe, mock_http):
        mock_http.add(responses.GET, GROQ_MODELS_URL, json=a_models_listing("openai/gpt-oss-20b", _LLM_MODEL))

        groq_probe.check()

    def test_lists_models_without_generating_tokens(self, groq_probe, mock_http):
        mock_http.add(responses.GET, GROQ_MODELS_URL, json=a_models_listing(_LLM_MODEL))

        groq_probe.check()

        request = mock_http.calls[0].request
        assert request.method == "GET"
        assert request.headers["Authorization"] == f"Bearer {_API_KEY}"
        assert request.req_kwargs["timeout"] == HEALTH_CHECK_TIMEOUT_SECONDS

    def test_fails_when_configured_model_was_retired(self, groq_probe, mock_http):
        mock_http.add(responses.GET, GROQ_MODELS_URL, json=a_models_listing("openai/gpt-oss-20b"))

        with pytest.raises(DependencyCheckError, match=f"'{_LLM_MODEL}' no está disponible"):
            groq_probe.check()

    def test_fails_on_http_error(self, groq_probe, mock_http):
        mock_http.add(responses.GET, GROQ_MODELS_URL, status=401)

        with pytest.raises(DependencyCheckError, match="HTTP 401"):
            groq_probe.check()


class TestSupabaseProbe:
    def test_passes_when_table_is_readable(self, supabase_probe, mock_http):
        mock_http.add(responses.GET, _SUPABASE_TABLE_URL, json=[])

        supabase_probe.check()

    def test_selects_a_single_row_with_short_timeout(self, supabase_probe, mock_http):
        mock_http.add(responses.GET, _SUPABASE_TABLE_URL, json=[])

        supabase_probe.check()

        request = mock_http.calls[0].request
        assert "limit=1" in request.url
        assert request.headers["apikey"] == _API_KEY
        assert request.req_kwargs["timeout"] == HEALTH_CHECK_TIMEOUT_SECONDS

    def test_fails_on_http_error(self, supabase_probe, mock_http):
        mock_http.add(responses.GET, _SUPABASE_TABLE_URL, status=503)

        with pytest.raises(DependencyCheckError, match="HTTP 503"):
            supabase_probe.check()
