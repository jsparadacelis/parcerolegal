"""Tests for dependency wiring."""

from __future__ import annotations

import pytest

from backend.app.api.dependencies import (
    _build_health_probes,
    _build_query_log_adapter,
    _build_query_log_store,
)
from backend.app.infrastructure.background_query_log_store import (
    BackgroundQueryLogStore,
)
from backend.app.infrastructure.config import Settings
from backend.app.infrastructure.health_probes import (
    GroqProbe,
    JinaProbe,
    QdrantProbe,
    SupabaseProbe,
)
from backend.app.infrastructure.supabase_query_log_store import (
    SupabaseQueryLogStore,
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


class TestBuildQueryLogAdapter:
    """El adapter crudo (sin el wrapper best-effort) respalda tanto el guardado
    (envuelto por _build_query_log_store) como la búsqueda por share_token
    (get_query_log_finder), que sí necesita propagar errores."""

    def test_returns_none_when_supabase_not_configured(self):
        assert _build_query_log_adapter(settings()) is None

    def test_returns_none_when_only_url_configured(self):
        assert _build_query_log_adapter(settings(supabase_url="https://proj.supabase.co")) is None

    def test_returns_supabase_store_when_configured(self):
        adapter = _build_query_log_adapter(
            settings(supabase_url="https://proj.supabase.co", supabase_key="key")
        )

        assert isinstance(adapter, SupabaseQueryLogStore)


class TestBuildHealthProbes:
    def test_probes_every_external_dependency(self):
        probes = _build_health_probes(settings())

        assert set(probes) == {"qdrant", "jina", "groq", "supabase"}

    def test_wires_the_concrete_probes(self):
        probes = _build_health_probes(
            settings(supabase_url="https://proj.supabase.co", supabase_key="key")
        )

        assert isinstance(probes["qdrant"], QdrantProbe)
        assert isinstance(probes["jina"], JinaProbe)
        assert isinstance(probes["groq"], GroqProbe)
        assert isinstance(probes["supabase"], SupabaseProbe)

    def test_supabase_is_skipped_when_not_configured(self):
        assert _build_health_probes(settings())["supabase"] is None
