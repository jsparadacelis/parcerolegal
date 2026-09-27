"""Tests for JinaEmbedder infrastructure adapter."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
import requests
import responses

from backend.app.domain.ports import ServiceBusyError
from backend.app.infrastructure.jina_embedder import JinaEmbedder

_JINA_API_KEY = "test-key"
_EMBED_URL = "https://api.jina.ai/v1/embeddings"


@pytest.fixture
def sleep() -> MagicMock:
    return MagicMock()


@pytest.fixture
def embedder(sleep) -> JinaEmbedder:
    return JinaEmbedder(api_key=_JINA_API_KEY, model="jina-embeddings-v3", dimensions=1024, sleep=sleep)


@pytest.fixture
def mock_http():
    with responses.RequestsMock() as r:
        yield r


def _jina_response(vector: list[float]) -> dict:
    return {"data": [{"embedding": vector}]}


class TestJinaEmbedder:
    def test_returns_list(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json=_jina_response([0.1] * 1024))

        result = embedder.embed("¿Qué es el habeas corpus?")

        assert isinstance(result, list)

    def test_returns_configured_dimensions(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json=_jina_response([float(i) for i in range(1024)]))

        result = embedder.embed("texto de prueba")

        assert len(result) == 1024

    def test_sends_auth_header(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json=_jina_response([0.1] * 1024))

        embedder.embed("test")

        assert mock_http.calls[0].request.headers["Authorization"] == f"Bearer {_JINA_API_KEY}"

    def test_sends_model_and_dimensions(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json=_jina_response([0.1] * 1024))

        embedder.embed("test")

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["model"] == "jina-embeddings-v3"
        assert sent["dimensions"] == 1024

    def test_uses_retrieval_query_task(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json=_jina_response([0.1] * 1024))

        embedder.embed("test")

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["task"] == "retrieval.query"

    def test_passes_text_as_input_list(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json=_jina_response([0.1] * 1024))

        embedder.embed("¿Cuáles son los derechos fundamentales?")

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["input"] == ["¿Cuáles son los derechos fundamentales?"]

    def test_raises_on_timeout(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, body=requests.exceptions.Timeout())

        with pytest.raises(requests.exceptions.Timeout):
            embedder.embed("texto")

    def test_retries_on_429_and_succeeds(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json={"detail": "rate limit"}, status=429)
        mock_http.add(responses.POST, _EMBED_URL, json=_jina_response([0.1] * 1024))

        result = embedder.embed("texto")

        assert len(result) == 1024
        assert len(mock_http.calls) == 2

    @pytest.mark.parametrize("status", [500, 502, 503, 504])
    def test_retries_on_transient_server_error_and_succeeds(self, embedder, mock_http, status):
        mock_http.add(responses.POST, _EMBED_URL, status=status)
        mock_http.add(responses.POST, _EMBED_URL, json=_jina_response([0.1] * 1024))

        embedder.embed("texto")

        assert len(mock_http.calls) == 2

    def test_retry_uses_exponential_backoff(self, embedder, sleep, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, status=429)
        mock_http.add(responses.POST, _EMBED_URL, status=429)
        mock_http.add(responses.POST, _EMBED_URL, json=_jina_response([0.1] * 1024))

        embedder.embed("texto")

        delays = [c.args[0] for c in sleep.call_args_list]
        assert delays[1] > delays[0]

    def test_raises_service_busy_after_max_retries_on_429(self, embedder, mock_http):
        for _ in range(3):
            mock_http.add(responses.POST, _EMBED_URL, status=429)

        with pytest.raises(ServiceBusyError):
            embedder.embed("texto")

        assert len(mock_http.calls) == 3

    def test_raises_http_error_when_server_errors_persist(self, embedder, mock_http):
        for _ in range(3):
            mock_http.add(responses.POST, _EMBED_URL, status=503)

        with pytest.raises(requests.HTTPError):
            embedder.embed("texto")

        assert len(mock_http.calls) == 3

    def test_does_not_retry_client_errors(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, status=401)

        with pytest.raises(requests.HTTPError):
            embedder.embed("texto")

        assert len(mock_http.calls) == 1
