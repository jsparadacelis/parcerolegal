"""Groq/Llama adapter — implements LLMClient port."""

from __future__ import annotations


class GroqLLMClient:
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int) -> None:
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(self, prompt: str) -> str:
        raise NotImplementedError
