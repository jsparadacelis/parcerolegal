"""Tests for SupabaseMissedQueryStore infrastructure adapter.

Corte a nivel HTTP con `responses`: el adapter habla el REST de Supabase
(PostgREST) vía `requests`, igual que el resto de adapters de infraestructura.
"""

from __future__ import annotations

import json

import pytest
import requests
import responses

from backend.app.domain.entities import MissedQuery
from backend.app.infrastructure.supabase_missed_query_store import (
    SupabaseMissedQueryStore,
)

_URL = "https://proj.supabase.co"
_API_KEY = "test-key"
_TABLE = "missed_queries"
_INSERT_URL = f"{_URL}/rest/v1/{_TABLE}"


def a_missed_query(
    question: str = "¿puedo quedarme con los bienes tras el divorcio?",
    answer: str = "Tu pregunta parece tratar sobre derecho de familia...",
    top_score: float | None = 0.38,
    detected_area: str | None = "derecho de familia y sucesiones (regulado por el Código Civil)",
    out_of_scope: bool = True,
) -> MissedQuery:
    return MissedQuery(
        question=question,
        answer=answer,
        top_score=top_score,
        detected_area=detected_area,
        out_of_scope=out_of_scope,
    )


@pytest.fixture
def store() -> SupabaseMissedQueryStore:
    return SupabaseMissedQueryStore(url=_URL, api_key=_API_KEY, table=_TABLE)


@pytest.fixture
def mock_http():
    with responses.RequestsMock() as r:
        yield r


class TestSupabaseMissedQueryStoreSave:
    def test_posts_serialized_missed_query_to_rest_endpoint(self, store, mock_http):
        mock_http.add(responses.POST, _INSERT_URL, status=201)

        store.save(
            a_missed_query(
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
            "top_score": 0.38,
            "detected_area": "derecho penal",
            "out_of_scope": True,
        }

    def test_sends_auth_and_representation_headers(self, store, mock_http):
        mock_http.add(responses.POST, _INSERT_URL, status=201)

        store.save(a_missed_query())

        headers = mock_http.calls[0].request.headers
        assert headers["apikey"] == _API_KEY
        assert headers["Authorization"] == f"Bearer {_API_KEY}"
        assert "return=minimal" in headers["Prefer"]

    def test_serializes_optional_fields_as_null_when_none(self, store, mock_http):
        mock_http.add(responses.POST, _INSERT_URL, status=201)

        store.save(a_missed_query(top_score=None, detected_area=None))

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["top_score"] is None
        assert sent["detected_area"] is None

    def test_swallows_and_logs_http_error(self, store, mock_http, caplog):
        mock_http.add(responses.POST, _INSERT_URL, json={"message": "boom"}, status=500)

        store.save(a_missed_query())  # best-effort: no debe propagar

        assert any(r.levelname == "WARNING" for r in caplog.records)

    def test_swallows_timeout(self, store, mock_http):
        mock_http.add(responses.POST, _INSERT_URL, body=requests.exceptions.Timeout())

        store.save(a_missed_query())  # best-effort: no debe propagar
