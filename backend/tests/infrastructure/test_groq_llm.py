"""Tests for GroqLLMClient infrastructure adapter."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
import requests
import responses

from backend.app.infrastructure.groq_llm import GroqLLMClient

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = "llama-3.1-70b-versatile"


def _groq_body(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


@pytest.fixture
def client() -> GroqLLMClient:
    return GroqLLMClient(
        api_key="test-key",
        model=_MODEL,
        temperature=0.0,
        max_tokens=1024,
    )


@pytest.fixture
def mock_http():
    with responses.RequestsMock() as r:
        yield r


class TestGroqLLMClientGenerate:
    def test_returns_content_from_api(self, client, mock_http):
        mock_http.add(responses.POST, _GROQ_URL, json=_groq_body("Respuesta legal."), status=200)

        assert client.generate("¿Qué es el habeas corpus?") == "Respuesta legal."

    def test_sends_correct_parameters_without_system(self, client, mock_http):
        mock_http.add(responses.POST, _GROQ_URL, json=_groq_body("ok"), status=200)

        client.generate("pregunta")

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["model"] == _MODEL
        assert sent["messages"] == [{"role": "user", "content": "pregunta"}]
        assert sent["temperature"] == 0.0
        assert sent["max_tokens"] == 1024

    def test_sends_system_message_when_provided(self, client, mock_http):
        mock_http.add(responses.POST, _GROQ_URL, json=_groq_body("ok"), status=200)

        client.generate("pregunta", system="Eres un asistente jurídico.")

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["messages"] == [
            {"role": "system", "content": "Eres un asistente jurídico."},
            {"role": "user", "content": "pregunta"},
        ]

    def test_omits_system_message_when_empty(self, client, mock_http):
        mock_http.add(responses.POST, _GROQ_URL, json=_groq_body("ok"), status=200)

        client.generate("pregunta")

        sent = json.loads(mock_http.calls[0].request.body)
        assert sent["messages"] == [{"role": "user", "content": "pregunta"}]

    def test_sends_auth_header(self, client, mock_http):
        mock_http.add(responses.POST, _GROQ_URL, json=_groq_body("ok"), status=200)

        client.generate("pregunta")

        assert mock_http.calls[0].request.headers["Authorization"] == "Bearer test-key"

    def test_retries_on_429_and_succeeds(self, client, mock_http):
        mock_http.add(responses.POST, _GROQ_URL, json={"error": "rate limit"}, status=429)
        mock_http.add(responses.POST, _GROQ_URL, json=_groq_body("Respuesta tras reintento."), status=200)

        with patch("backend.app.infrastructure.groq_llm.time.sleep"):
            result = client.generate("pregunta")

        assert result == "Respuesta tras reintento."
        assert len(mock_http.calls) == 2

    def test_raises_after_max_retries(self, client, mock_http):
        for _ in range(3):
            mock_http.add(responses.POST, _GROQ_URL, json={"error": "rate limit"}, status=429)

        with patch("backend.app.infrastructure.groq_llm.time.sleep"):
            with pytest.raises(Exception):
                client.generate("pregunta")

        assert len(mock_http.calls) == 3

    def test_raises_immediately_on_non_429_error(self, client, mock_http):
        mock_http.add(responses.POST, _GROQ_URL, json={"error": "server error"}, status=500)

        with pytest.raises(Exception):
            client.generate("pregunta")

        assert len(mock_http.calls) == 1

    def test_raises_on_empty_response_content(self, client, mock_http):
        mock_http.add(responses.POST, _GROQ_URL, json=_groq_body(""), status=200)

        with pytest.raises(ValueError, match="vacía"):
            client.generate("pregunta")

    def test_retry_uses_exponential_backoff(self, client, mock_http):
        mock_http.add(responses.POST, _GROQ_URL, json={"error": "rl"}, status=429)
        mock_http.add(responses.POST, _GROQ_URL, json={"error": "rl"}, status=429)
        mock_http.add(responses.POST, _GROQ_URL, json=_groq_body("ok"), status=200)

        with patch("backend.app.infrastructure.groq_llm.time.sleep") as mock_sleep:
            client.generate("pregunta")

        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays[1] > delays[0]

    def test_raises_on_timeout(self, client, mock_http):
        mock_http.add(responses.POST, _GROQ_URL, body=requests.exceptions.Timeout())

        with pytest.raises(requests.exceptions.Timeout):
            client.generate("pregunta")
