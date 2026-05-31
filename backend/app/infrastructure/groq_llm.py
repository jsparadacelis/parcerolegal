"""Groq/Llama adapter — implements LLMClient port via direct HTTP."""

from __future__ import annotations

import time

import requests

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


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

        for attempt in range(_MAX_RETRIES):
            response = requests.post(_GROQ_URL, json=payload, headers=self._headers)
            if response.status_code == 429:
                last_response = response
                time.sleep(_BASE_DELAY * (2 ** attempt))
                continue
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            if not content:
                raise ValueError("La respuesta del LLM está vacía")
            return content

        last_response.raise_for_status()
