"""Groq/Llama adapter — implements LLMClient port via direct HTTP."""

from __future__ import annotations

import re
import time
from collections.abc import Callable

from backend.app.infrastructure.config import (
    GROQ_CHAT_COMPLETIONS_URL,
    GROQ_INCLUDE_REASONING,
    GROQ_MAX_RETRIES,
    GROQ_MAX_RETRY_WAIT_SECONDS,
    GROQ_REASONING_EFFORT,
    GROQ_RETRY_BASE_DELAY_SECONDS,
    GROQ_TIMEOUT_SECONDS,
    HTTP_TOO_MANY_REQUESTS,
)
from backend.app.infrastructure.http_retry import RetryPolicy, post_with_retries

# gpt-oss cita con corchetes de ancho completo (【2】, 【2†L3-L5】) aunque el
# prompt pida [2]; se normalizan para que sanitize_citations las valide.
_FULLWIDTH_CITATION_PATTERN = re.compile(r"【(\d+)(?:†[^】]*)?】")

# Solo 429: un 5xx de Groq tras ~10s de generación no vale la pena repetirlo
# dentro del mismo request del usuario.
_RETRY_POLICY = RetryPolicy(
    max_attempts=GROQ_MAX_RETRIES,
    base_delay_seconds=GROQ_RETRY_BASE_DELAY_SECONDS,
    max_total_wait_seconds=GROQ_MAX_RETRY_WAIT_SECONDS,
    retryable_statuses=frozenset({HTTP_TOO_MANY_REQUESTS}),
)


class GroqLLMClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float,
        max_tokens: int,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._model = model
        self._sleep = sleep
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
            "reasoning_effort": GROQ_REASONING_EFFORT,
            "include_reasoning": GROQ_INCLUDE_REASONING,
        }

        response = post_with_retries(
            GROQ_CHAT_COMPLETIONS_URL,
            payload=payload,
            headers=self._headers,
            timeout=GROQ_TIMEOUT_SECONDS,
            policy=_RETRY_POLICY,
            sleep=self._sleep,
        )
        content = response.json()["choices"][0]["message"]["content"]
        if not content:
            raise ValueError("La respuesta del LLM está vacía")
        return _FULLWIDTH_CITATION_PATTERN.sub(r"[\1]", content)
