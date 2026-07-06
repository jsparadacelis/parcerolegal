"""Groq/Llama adapter — implements LLMClient port via direct HTTP."""

from __future__ import annotations

import time

import requests

from backend.app.infrastructure.config import (
    GROQ_CHAT_COMPLETIONS_URL,
    GROQ_MAX_RETRIES,
    GROQ_RETRY_BASE_DELAY_SECONDS,
    GROQ_TIMEOUT_SECONDS,
    HTTP_TOO_MANY_REQUESTS,
)


class GroqLLMClient:
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int) -> None:
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }

        last_response: requests.Response | None = None

        for attempt in range(GROQ_MAX_RETRIES):
            response = requests.post(
                GROQ_CHAT_COMPLETIONS_URL, json=payload, headers=self._headers, timeout=GROQ_TIMEOUT_SECONDS
            )
            if response.status_code == HTTP_TOO_MANY_REQUESTS:
                last_response = response
                time.sleep(GROQ_RETRY_BASE_DELAY_SECONDS * (2 ** attempt))
                continue
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            if not content:
                raise ValueError("La respuesta del LLM está vacía")
            return content

        last_response.raise_for_status()
