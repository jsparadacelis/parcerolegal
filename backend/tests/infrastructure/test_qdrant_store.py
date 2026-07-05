"""Tests for QdrantVectorStore infrastructure adapter."""
from __future__ import annotations

import json

import pytest
import responses

from backend.app.domain.entities import RetrievedChunk
from backend.app.infrastructure.qdrant_store import QdrantVectorStore

_URL = "https://my.qdrant.io"
_COLLECTION = "parcerolegal"
_SEARCH_URL = f"{_URL}/collections/{_COLLECTION}/points/search"


def _qdrant_result(
    point_id: str,
    score: float,
    text: str,
    source_type: str,
    extra: dict | None = None,
) -> dict:
    return {
        "id": point_id,
        "score": score,
        "payload": {"text": text, "source_type": source_type, **(extra or {})},
    }


def _qdrant_response(results: list[dict]) -> dict:
    return {"result": results, "status": "ok", "time": 0.001}


@pytest.fixture
def store() -> QdrantVectorStore:
    return QdrantVectorStore(url=_URL, api_key="test-key", collection=_COLLECTION)


@pytest.fixture
def mock_http():
    with responses.RequestsMock() as r:
        yield r


class TestQdrantVectorStoreSearch:
    def test_returns_list_of_retrieved_chunks(self, store, mock_http):
        mock_http.add(responses.POST, _SEARCH_URL, json=_qdrant_response([
            _qdrant_result("id-1", 0.85, "texto", "constitucion"),
        ]))

        result = store.search([0.1] * 384)

        assert len(result) == 1
        assert isinstance(result[0], RetrievedChunk)

    def test_maps_constitucion_payload(self, store, mock_http):
        mock_http.add(responses.POST, _SEARCH_URL, json=_qdrant_response([
            _qdrant_result("id-1", 0.85, "Texto del artículo.", "constitucion", extra={
                "article_numero": "13",
                "titulo": "Igualdad",
                "url_original": "http://example.com/art13",
            }),
        ]))

        chunk = store.search([0.1] * 384)[0]

        assert chunk.chunk_id == "id-1"
        assert chunk.text == "Texto del artículo."
        assert chunk.score == 0.85
        assert chunk.source_type == "constitucion"
        assert chunk.metadata["article_numero"] == "13"
        assert chunk.metadata["url_original"] == "http://example.com/art13"

    def test_maps_sentencia_payload(self, store, mock_http):
        mock_http.add(responses.POST, _SEARCH_URL, json=_qdrant_response([
            _qdrant_result("id-2", 0.78, "Texto de sentencia.", "sentencia", extra={
                "sentencia_id": "T-760-2008",
                "source_url": "http://corte.gov.co/T-760",
            }),
        ]))

        chunk = store.search([0.1] * 384)[0]

        assert chunk.source_type == "sentencia"
        assert chunk.metadata["sentencia_id"] == "T-760-2008"
        assert chunk.metadata["source_url"] == "http://corte.gov.co/T-760"

    def test_metadata_excludes_text_and_source_type(self, store, mock_http):
        mock_http.add(responses.POST, _SEARCH_URL, json=_qdrant_response([
            _qdrant_result("id-1", 0.9, "texto", "constitucion", extra={"titulo": "T"}),
        ]))

        chunk = store.search([0.1] * 384)[0]

        assert "text" not in chunk.metadata
        assert "source_type" not in chunk.metadata

    def test_passes_top_k_to_qdrant(self, store, mock_http):
        mock_http.add(responses.POST, _SEARCH_URL, json=_qdrant_response([]))

        store.search([0.1] * 384, top_k=3)

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["limit"] == 3

    def test_default_top_k_is_5(self, store, mock_http):
        mock_http.add(responses.POST, _SEARCH_URL, json=_qdrant_response([]))

        store.search([0.1] * 384)

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["limit"] == 5

    def test_sends_auth_header(self, store, mock_http):
        mock_http.add(responses.POST, _SEARCH_URL, json=_qdrant_response([]))

        store.search([0.1] * 384)

        assert mock_http.calls[0].request.headers["api-key"] == "test-key"

    def test_returns_empty_list_when_no_results(self, store, mock_http):
        mock_http.add(responses.POST, _SEARCH_URL, json=_qdrant_response([]))

        assert store.search([0.1] * 384) == []

    def test_no_filter_sent_when_sentencia_id_omitted(self, store, mock_http):
        mock_http.add(responses.POST, _SEARCH_URL, json=_qdrant_response([]))

        store.search([0.1] * 384)

        sent = json.loads(mock_http.calls[0].request.body)
        assert "filter" not in sent

    def test_sends_sentencia_id_filter(self, store, mock_http):
        mock_http.add(responses.POST, _SEARCH_URL, json=_qdrant_response([]))

        store.search([0.1] * 384, sentencia_id="T-760-08")

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["filter"] == {"must": [{"key": "sentencia_id", "match": {"value": "T-760-08"}}]}
