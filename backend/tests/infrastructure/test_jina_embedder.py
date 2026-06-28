"""Tests for JinaEmbedder infrastructure adapter."""
from __future__ import annotations

import json

import pytest
import requests
import responses

from backend.app.infrastructure.jina_embedder import JinaEmbedder

_JINA_API_KEY = "test-key"
_EMBED_URL = "https://api.jina.ai/v1/embeddings"


@pytest.fixture
def embedder() -> JinaEmbedder:
    return JinaEmbedder(api_key=_JINA_API_KEY, model="jina-embeddings-v3", dimensions=1024)


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
