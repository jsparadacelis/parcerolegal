"""Groq/Llama adapter — implements LLMClient port."""

from __future__ import annotations

import time

import groq


_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class GroqLLMClient:
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int) -> None:
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._groq = groq.Groq(api_key=api_key)

    def generate(self, prompt: str) -> str:
        last_error: groq.RateLimitError | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                response = self._groq.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                )
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("La respuesta del LLM está vacía")
                return content
            except groq.RateLimitError as exc:
                last_error = exc
                time.sleep(_BASE_DELAY * (2**attempt))

        raise last_error
