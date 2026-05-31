"""Tests for SentenceTransformerEmbedder infrastructure adapter."""
from __future__ import annotations

import json

import pytest
import responses

from backend.app.infrastructure.st_embedder import SentenceTransformerEmbedder

_MODEL = "ibm-granite/granite-embedding-97m-multilingual-r2"
_HF_TOKEN = "test-token"
_EMBED_URL = f"https://router.huggingface.co/hf-inference/pipeline/feature-extraction/{_MODEL}"


@pytest.fixture
def embedder() -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder(model_name=_MODEL, hf_token=_HF_TOKEN)


@pytest.fixture
def mock_http():
    with responses.RequestsMock() as r:
        yield r


class TestSentenceTransformerEmbedder:
    def test_returns_list(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json=[[0.1] * 384])

        result = embedder.embed("¿Qué es el habeas corpus?")

        assert isinstance(result, list)

    def test_returns_384_dimensions(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json=[[float(i) for i in range(384)]])

        result = embedder.embed("texto de prueba")

        assert len(result) == 384

    def test_passes_text_to_model(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json=[[0.1] * 384])

        embedder.embed("¿Cuáles son los derechos fundamentales?")

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["inputs"] == "¿Cuáles son los derechos fundamentales?"

    def test_sends_auth_header(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json=[[0.1] * 384])

        embedder.embed("test")

        assert mock_http.calls[0].request.headers["Authorization"] == f"Bearer {_HF_TOKEN}"

    def test_builds_correct_url(self, embedder, mock_http):
        mock_http.add(responses.POST, _EMBED_URL, json=[[0.1] * 384])

        embedder.embed("test")

        assert mock_http.calls[0].request.url == _EMBED_URL
