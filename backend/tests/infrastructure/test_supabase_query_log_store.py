"""Tests for SupabaseQueryLogStore infrastructure adapter.

Corte a nivel HTTP con `responses`: el adapter habla el REST de Supabase
(PostgREST) vía `requests`, igual que el resto de adapters de infraestructura.
"""

from __future__ import annotations

import json

import pytest
import requests
import responses

from backend.app.domain.entities import QueryLog, Source
from backend.app.infrastructure.supabase_query_log_store import (
    SupabaseQueryLogStore,
)

_URL = "https://proj.supabase.co"
_API_KEY = "test-key"
_TABLE = "queries"
_INSERT_URL = f"{_URL}/rest/v1/{_TABLE}"


def a_source() -> Source:
    return Source(
        chunk_id="c1",
        source_type="constitucion",
        title="Art. 30",
        url="https://example.com/art30",
    )


def a_query_log(
    question: str = "¿puedo quedarme con los bienes tras el divorcio?",
    answer: str = "Tu pregunta parece tratar sobre derecho de familia...",
    sources: list[Source] | None = None,
    top_score: float | None = 0.38,
    detected_area: str | None = "derecho de familia y sucesiones (regulado por el Código Civil)",
    out_of_scope: bool = True,
) -> QueryLog:
    return QueryLog(
        question=question,
        answer=answer,
        sources=sources if sources is not None else [],
        top_score=top_score,
        detected_area=detected_area,
        out_of_scope=out_of_scope,
    )


@pytest.fixture
def store() -> SupabaseQueryLogStore:
    return SupabaseQueryLogStore(url=_URL, api_key=_API_KEY, table=_TABLE)


@pytest.fixture
def mock_http():
    with responses.RequestsMock() as r:
        yield r


class TestSupabaseQueryLogStoreSave:
    def test_posts_serialized_query_log_to_rest_endpoint(self, store, mock_http):
        mock_http.add(responses.POST, _INSERT_URL, status=201)

        store.save(
            a_query_log(
                question="pregunta X",
                answer="respuesta Y",
                top_score=0.38,
                detected_area="derecho penal",
                out_of_scope=True,
            )
        )

        request = mock_http.calls[0].request
        assert request.url == _INSERT_URL
        sent = json.loads(request.body)
        assert sent == {
            "question": "pregunta X",
            "answer": "respuesta Y",
            "sources": [],
            "top_score": 0.38,
            "detected_area": "derecho penal",
            "out_of_scope": True,
        }

    def test_posts_sources_as_list_of_dicts(self, store, mock_http):
        mock_http.add(responses.POST, _INSERT_URL, status=201)

        store.save(a_query_log(sources=[a_source()], out_of_scope=False))

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["sources"] == [
            {
                "chunk_id": "c1",
                "source_type": "constitucion",
                "title": "Art. 30",
                "url": "https://example.com/art30",
            }
        ]

    def test_sends_auth_and_representation_headers(self, store, mock_http):
        mock_http.add(responses.POST, _INSERT_URL, status=201)

        store.save(a_query_log())

        headers = mock_http.calls[0].request.headers
        assert headers["apikey"] == _API_KEY
        assert headers["Authorization"] == f"Bearer {_API_KEY}"
        assert "return=minimal" in headers["Prefer"]

    def test_serializes_optional_fields_as_null_when_none(self, store, mock_http):
        mock_http.add(responses.POST, _INSERT_URL, status=201)

        store.save(a_query_log(top_score=None, detected_area=None))

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["top_score"] is None
        assert sent["detected_area"] is None

    def test_swallows_and_logs_http_error(self, store, mock_http, caplog):
        mock_http.add(responses.POST, _INSERT_URL, json={"message": "boom"}, status=500)

        store.save(a_query_log())  # best-effort: no debe propagar

        assert any(r.levelname == "WARNING" for r in caplog.records)

    def test_swallows_timeout(self, store, mock_http):
        mock_http.add(responses.POST, _INSERT_URL, body=requests.exceptions.Timeout())

        store.save(a_query_log())  # best-effort: no debe propagar
