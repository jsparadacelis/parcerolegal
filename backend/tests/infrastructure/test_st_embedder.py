"""Tests for SentenceTransformerEmbedder infrastructure adapter."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.app.infrastructure.st_embedder import SentenceTransformerEmbedder

_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _make_embedder() -> tuple[SentenceTransformerEmbedder, MagicMock]:
    with patch("backend.app.infrastructure.st_embedder.SentenceTransformer") as MockST:
        mock_model = MagicMock()
        mock_model.encode.return_value = [0.1] * 384
        MockST.return_value = mock_model
        embedder = SentenceTransformerEmbedder(model_name=_MODEL)
    return embedder, mock_model


class TestSentenceTransformerEmbedder:
    def test_returns_list(self):
        embedder, _ = _make_embedder()
        result = embedder.embed("¿Qué es el habeas corpus?")
        assert isinstance(result, list)

    def test_returns_384_dimensions(self):
        embedder, _ = _make_embedder()
        result = embedder.embed("texto de prueba")
        assert len(result) == 384

    def test_passes_text_to_model(self):
        embedder, mock_model = _make_embedder()
        embedder.embed("¿Cuáles son los derechos fundamentales?")
        mock_model.encode.assert_called_once_with("¿Cuáles son los derechos fundamentales?")

    def test_model_loaded_once_on_init(self):
        with patch("backend.app.infrastructure.st_embedder.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.encode.return_value = [0.0] * 384
            MockST.return_value = mock_model

            embedder = SentenceTransformerEmbedder(model_name=_MODEL)
            embedder.embed("pregunta 1")
            embedder.embed("pregunta 2")

            MockST.assert_called_once_with(_MODEL)

    def test_initializes_with_correct_model_name(self):
        with patch("backend.app.infrastructure.st_embedder.SentenceTransformer") as MockST:
            MockST.return_value = MagicMock()
            SentenceTransformerEmbedder(model_name=_MODEL)
            MockST.assert_called_once_with(_MODEL)
