"""Tests for SentenceTransformerEmbedder infrastructure adapter."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.app.infrastructure.st_embedder import SentenceTransformerEmbedder

_MODEL = "ibm-granite/granite-embedding-97m-multilingual-r2"
_HF_TOKEN = "test-token"


def _mock_response(dims: int = 384) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = [[float(i) for i in range(dims)]]
    return resp


class TestSentenceTransformerEmbedder:
    def test_returns_list(self):
        with patch("backend.app.infrastructure.st_embedder.httpx.post") as mock_post:
            mock_post.return_value = _mock_response()
            embedder = SentenceTransformerEmbedder(model_name=_MODEL, hf_token=_HF_TOKEN)
            result = embedder.embed("¿Qué es el habeas corpus?")
        assert isinstance(result, list)

    def test_returns_384_dimensions(self):
        with patch("backend.app.infrastructure.st_embedder.httpx.post") as mock_post:
            mock_post.return_value = _mock_response(384)
            embedder = SentenceTransformerEmbedder(model_name=_MODEL, hf_token=_HF_TOKEN)
            result = embedder.embed("texto de prueba")
        assert len(result) == 384

    def test_passes_text_to_model(self):
        with patch("backend.app.infrastructure.st_embedder.httpx.post") as mock_post:
            mock_post.return_value = _mock_response()
            embedder = SentenceTransformerEmbedder(model_name=_MODEL, hf_token=_HF_TOKEN)
            embedder.embed("¿Cuáles son los derechos fundamentales?")
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["inputs"] == "¿Cuáles son los derechos fundamentales?"

    def test_sends_auth_header(self):
        with patch("backend.app.infrastructure.st_embedder.httpx.post") as mock_post:
            mock_post.return_value = _mock_response()
            embedder = SentenceTransformerEmbedder(model_name=_MODEL, hf_token=_HF_TOKEN)
            embedder.embed("test")
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["Authorization"] == f"Bearer {_HF_TOKEN}"

    def test_builds_correct_url(self):
        with patch("backend.app.infrastructure.st_embedder.httpx.post") as mock_post:
            mock_post.return_value = _mock_response()
            embedder = SentenceTransformerEmbedder(model_name=_MODEL, hf_token=_HF_TOKEN)
            embedder.embed("test")
        url = mock_post.call_args[0][0]
        assert _MODEL in url
        assert "feature-extraction" in url
