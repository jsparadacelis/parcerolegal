"""Tests for GroqLLMClient infrastructure adapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import groq
import pytest

from backend.app.infrastructure.groq_llm import GroqLLMClient


def _make_groq_response(content: str) -> MagicMock:
    response = MagicMock()
    response.choices[0].message.content = content
    return response


@pytest.fixture
def client() -> GroqLLMClient:
    return GroqLLMClient(
        api_key="test-key",
        model="llama-3.1-70b-versatile",
        temperature=0.0,
        max_tokens=1024,
    )


class TestGroqLLMClientGenerate:
    def test_returns_content_from_api(self, client):
        mock_groq = MagicMock()
        mock_groq.chat.completions.create.return_value = _make_groq_response("Respuesta legal.")
        client._groq = mock_groq

        result = client.generate("¿Qué es el habeas corpus?")

        assert result == "Respuesta legal."

    def test_sends_correct_parameters(self, client):
        mock_groq = MagicMock()
        mock_groq.chat.completions.create.return_value = _make_groq_response("ok")
        client._groq = mock_groq

        client.generate("pregunta")

        mock_groq.chat.completions.create.assert_called_once_with(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": "pregunta"}],
            temperature=0.0,
            max_tokens=1024,
        )

    def test_retries_on_rate_limit_and_succeeds(self, client):
        mock_groq = MagicMock()
        mock_groq.chat.completions.create.side_effect = [
            groq.RateLimitError("rate limit", response=MagicMock(), body={}),
            _make_groq_response("Respuesta tras reintento."),
        ]
        client._groq = mock_groq

        with patch("backend.app.infrastructure.groq_llm.time.sleep"):
            result = client.generate("pregunta")

        assert result == "Respuesta tras reintento."
        assert mock_groq.chat.completions.create.call_count == 2

    def test_raises_after_max_retries(self, client):
        mock_groq = MagicMock()
        rate_limit_err = groq.RateLimitError("rate limit", response=MagicMock(), body={})
        mock_groq.chat.completions.create.side_effect = [rate_limit_err] * 4
        client._groq = mock_groq

        with patch("backend.app.infrastructure.groq_llm.time.sleep"):
            with pytest.raises(groq.RateLimitError):
                client.generate("pregunta")

        assert mock_groq.chat.completions.create.call_count == 3

    def test_raises_immediately_on_non_rate_limit_error(self, client):
        mock_groq = MagicMock()
        mock_groq.chat.completions.create.side_effect = groq.APIConnectionError(request=MagicMock())
        client._groq = mock_groq

        with pytest.raises(groq.APIConnectionError):
            client.generate("pregunta")

        assert mock_groq.chat.completions.create.call_count == 1

    def test_raises_on_empty_response_content(self, client):
        mock_groq = MagicMock()
        mock_groq.chat.completions.create.return_value = _make_groq_response("")
        client._groq = mock_groq

        with pytest.raises(ValueError, match="vacía"):
            client.generate("pregunta")

    def test_sleep_uses_exponential_backoff(self, client):
        mock_groq = MagicMock()
        mock_groq.chat.completions.create.side_effect = [
            groq.RateLimitError("rl", response=MagicMock(), body={}),
            groq.RateLimitError("rl", response=MagicMock(), body={}),
            _make_groq_response("ok"),
        ]
        client._groq = mock_groq

        with patch("backend.app.infrastructure.groq_llm.time.sleep") as mock_sleep:
            client.generate("pregunta")

        sleep_calls = [c.args[0] for c in mock_sleep.call_args_list]
        assert sleep_calls[1] > sleep_calls[0], "second delay should be longer than first"
