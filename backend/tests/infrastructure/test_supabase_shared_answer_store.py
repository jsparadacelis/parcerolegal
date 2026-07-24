"""Tests for SupabaseSharedAnswerStore infrastructure adapter.

Corte a nivel HTTP con `responses`: el adapter habla el REST de Supabase
(PostgREST) vía `requests`, igual que el resto de adapters de infraestructura.
A diferencia de SupabaseMissedQueryStore, los errores deben PROPAGARSE, no
tragarse — ver domain.ports.SharedAnswerStore.
"""

from __future__ import annotations

import json

import pytest
import requests
import responses

from backend.app.domain.entities import SharedAnswer, Source
from backend.app.infrastructure.supabase_shared_answer_store import (
    SupabaseSharedAnswerStore,
)

_URL = "https://proj.supabase.co"
_API_KEY = "test-key"
_TABLE = "shared_answers"
_TABLE_URL = f"{_URL}/rest/v1/{_TABLE}"


def a_source() -> Source:
    return Source(
        chunk_id="c1",
        source_type="constitucion",
        title="Art. 30",
        url="https://example.com/art30",
    )


def a_shared_answer(
    id: str = "kJ3f9xQb2p1",
    question: str = "¿Qué es el habeas corpus?",
    answer: str = "El habeas corpus es un derecho fundamental.",
    sources: list[Source] | None = None,
    out_of_scope: bool = False,
) -> SharedAnswer:
    return SharedAnswer(
        id=id,
        question=question,
        answer=answer,
        sources=sources if sources is not None else [a_source()],
        out_of_scope=out_of_scope,
    )


@pytest.fixture
def store() -> SupabaseSharedAnswerStore:
    return SupabaseSharedAnswerStore(url=_URL, api_key=_API_KEY, table=_TABLE)


@pytest.fixture
def mock_http():
    with responses.RequestsMock() as r:
        yield r


class TestSupabaseSharedAnswerStoreSave:
    def test_posts_serialized_shared_answer_to_rest_endpoint(self, store, mock_http):
        mock_http.add(responses.POST, _TABLE_URL, status=201)

        store.save(a_shared_answer(id="id-1", question="pregunta X", answer="respuesta Y"))

        request = mock_http.calls[0].request
        assert request.url == _TABLE_URL
        sent = json.loads(request.body)
        assert sent == {
            "id": "id-1",
            "question": "pregunta X",
            "answer": "respuesta Y",
            "sources": [
                {
                    "chunk_id": "c1",
                    "source_type": "constitucion",
                    "title": "Art. 30",
                    "url": "https://example.com/art30",
                }
            ],
            "out_of_scope": False,
        }

    def test_sends_auth_and_representation_headers(self, store, mock_http):
        mock_http.add(responses.POST, _TABLE_URL, status=201)

        store.save(a_shared_answer())

        headers = mock_http.calls[0].request.headers
        assert headers["apikey"] == _API_KEY
        assert headers["Authorization"] == f"Bearer {_API_KEY}"
        assert "return=minimal" in headers["Prefer"]

    def test_raises_on_http_error(self, store, mock_http):
        mock_http.add(responses.POST, _TABLE_URL, json={"message": "boom"}, status=500)

        with pytest.raises(requests.exceptions.HTTPError):
            store.save(a_shared_answer())

    def test_raises_on_timeout(self, store, mock_http):
        mock_http.add(responses.POST, _TABLE_URL, body=requests.exceptions.Timeout())

        with pytest.raises(requests.exceptions.Timeout):
            store.save(a_shared_answer())


class TestSupabaseSharedAnswerStoreGet:
    def test_returns_shared_answer_when_found(self, store, mock_http):
        mock_http.add(
            responses.GET,
            _TABLE_URL,
            json=[
                {
                    "id": "kJ3f9xQb2p1",
                    "question": "¿Qué es el habeas corpus?",
                    "answer": "El habeas corpus es un derecho fundamental.",
                    "sources": [
                        {
                            "chunk_id": "c1",
                            "source_type": "constitucion",
                            "title": "Art. 30",
                            "url": "https://example.com/art30",
                        }
                    ],
                    "out_of_scope": False,
                }
            ],
            status=200,
        )

        shared = store.get("kJ3f9xQb2p1")

        assert shared == a_shared_answer()

    def test_sends_id_filter_and_auth_headers(self, store, mock_http):
        mock_http.add(responses.GET, _TABLE_URL, json=[], status=200)

        store.get("kJ3f9xQb2p1")

        request = mock_http.calls[0].request
        assert "id=eq.kJ3f9xQb2p1" in request.url
        assert request.headers["apikey"] == _API_KEY
        assert request.headers["Authorization"] == f"Bearer {_API_KEY}"

    def test_returns_none_when_not_found(self, store, mock_http):
        mock_http.add(responses.GET, _TABLE_URL, json=[], status=200)

        assert store.get("no-existe") is None

    def test_raises_on_http_error(self, store, mock_http):
        mock_http.add(responses.GET, _TABLE_URL, json={"message": "boom"}, status=500)

        with pytest.raises(requests.exceptions.HTTPError):
            store.get("kJ3f9xQb2p1")

    def test_raises_on_timeout(self, store, mock_http):
        mock_http.add(responses.GET, _TABLE_URL, body=requests.exceptions.Timeout())

        with pytest.raises(requests.exceptions.Timeout):
            store.get("kJ3f9xQb2p1")
