"""Tests for QdrantVectorStore infrastructure adapter."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.app.domain.entities import RetrievedChunk
from backend.app.infrastructure.qdrant_store import QdrantVectorStore


def _make_scored_point(
    point_id: str,
    score: float,
    text: str,
    source_type: str,
    extra: dict | None = None,
) -> MagicMock:
    point = MagicMock()
    point.id = point_id
    point.score = score
    point.payload = {"text": text, "source_type": source_type, **(extra or {})}
    return point


@pytest.fixture
def store() -> QdrantVectorStore:
    with patch("backend.app.infrastructure.qdrant_store.QdrantClient"):
        s = QdrantVectorStore(
            url="http://localhost:6333",
            api_key="test-key",
            collection="parcerolegal",
        )
    return s


class TestQdrantVectorStoreSearch:
    def test_returns_list_of_retrieved_chunks(self, store):
        store._client.search.return_value = [
            _make_scored_point("id-1", 0.85, "texto", "constitucion")
        ]
        result = store.search([0.1] * 384)
        assert len(result) == 1
        assert isinstance(result[0], RetrievedChunk)

    def test_maps_constitucion_payload(self, store):
        store._client.search.return_value = [
            _make_scored_point(
                "id-1",
                0.85,
                "Texto del artículo.",
                "constitucion",
                extra={
                    "article_numero": "13",
                    "titulo": "Igualdad",
                    "url_original": "http://example.com/art13",
                },
            )
        ]
        chunk = store.search([0.1] * 384)[0]
        assert chunk.chunk_id == "id-1"
        assert chunk.text == "Texto del artículo."
        assert chunk.score == 0.85
        assert chunk.source_type == "constitucion"
        assert chunk.metadata["article_numero"] == "13"
        assert chunk.metadata["url_original"] == "http://example.com/art13"

    def test_maps_sentencia_payload(self, store):
        store._client.search.return_value = [
            _make_scored_point(
                "id-2",
                0.78,
                "Texto de sentencia.",
                "sentencia",
                extra={
                    "sentencia_id": "T-760-2008",
                    "source_url": "http://corte.gov.co/T-760",
                },
            )
        ]
        chunk = store.search([0.1] * 384)[0]
        assert chunk.source_type == "sentencia"
        assert chunk.metadata["sentencia_id"] == "T-760-2008"
        assert chunk.metadata["source_url"] == "http://corte.gov.co/T-760"

    def test_metadata_excludes_text_and_source_type(self, store):
        store._client.search.return_value = [
            _make_scored_point("id-1", 0.9, "texto", "constitucion", extra={"titulo": "T"})
        ]
        chunk = store.search([0.1] * 384)[0]
        assert "text" not in chunk.metadata
        assert "source_type" not in chunk.metadata

    def test_passes_top_k_to_qdrant(self, store):
        store._client.search.return_value = []
        store.search([0.1] * 384, top_k=3)
        store._client.search.assert_called_once_with(
            collection_name="parcerolegal",
            query_vector=[0.1] * 384,
            limit=3,
        )

    def test_default_top_k_is_5(self, store):
        store._client.search.return_value = []
        store.search([0.1] * 384)
        _, kwargs = store._client.search.call_args
        assert kwargs["limit"] == 5

    def test_returns_empty_list_when_no_results(self, store):
        store._client.search.return_value = []
        assert store.search([0.1] * 384) == []

    def test_initializes_client_with_credentials(self):
        with patch("backend.app.infrastructure.qdrant_store.QdrantClient") as MockClient:
            QdrantVectorStore(url="https://my.qdrant.io", api_key="secret", collection="col")
            MockClient.assert_called_once_with(url="https://my.qdrant.io", api_key="secret")
