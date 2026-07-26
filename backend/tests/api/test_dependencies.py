"""Tests for dependency wiring."""

from __future__ import annotations

import pytest

from backend.app.api.dependencies import _build_query_log_store, _build_shared_answer_store
from backend.app.infrastructure.background_query_log_store import (
    BackgroundQueryLogStore,
)
from backend.app.infrastructure.config import Settings
from backend.app.infrastructure.supabase_shared_answer_store import (
    SupabaseSharedAnswerStore,
)


def settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


class TestBuildQueryLogStore:
    def test_returns_none_when_supabase_not_configured(self):
        assert _build_query_log_store(settings()) is None

    def test_returns_none_when_only_url_configured(self):
        assert _build_query_log_store(settings(supabase_url="https://proj.supabase.co")) is None

    def test_returns_background_store_when_configured(self):
        store = _build_query_log_store(
            settings(supabase_url="https://proj.supabase.co", supabase_key="key")
        )

        assert isinstance(store, BackgroundQueryLogStore)


class TestBuildSharedAnswerStore:
    def test_returns_none_when_supabase_not_configured(self):
        assert _build_shared_answer_store(settings()) is None

    def test_returns_none_when_only_url_configured(self):
        assert _build_shared_answer_store(settings(supabase_url="https://proj.supabase.co")) is None

    def test_returns_supabase_store_when_configured(self):
        store = _build_shared_answer_store(
            settings(supabase_url="https://proj.supabase.co", supabase_key="key")
        )

        assert isinstance(store, SupabaseSharedAnswerStore)
