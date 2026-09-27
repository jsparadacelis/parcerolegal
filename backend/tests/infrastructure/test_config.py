"""Tests for backend Settings defaults."""

from __future__ import annotations

import pytest

from backend.app.infrastructure.config import Settings


@pytest.fixture
def settings(monkeypatch) -> Settings:
    monkeypatch.delenv("LLM_MODEL", raising=False)
    return Settings(_env_file=None)


class TestSettingsDefaults:
    def test_llm_model_default_is_available_groq_model(self, settings):
        assert settings.llm_model == "openai/gpt-oss-120b"
