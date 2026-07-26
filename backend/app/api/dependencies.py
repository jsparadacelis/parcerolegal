"""FastAPI dependency injection — wires infrastructure to use cases."""

from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException

from backend.app.application.get_shared_query_use_case import GetSharedQueryUseCase
from backend.app.application.query_use_case import QueryUseCase
from backend.app.domain.ports import QueryLogFinder, QueryLogStore
from backend.app.infrastructure.background_query_log_store import (
    BackgroundQueryLogStore,
)
from backend.app.infrastructure.config import Settings
from backend.app.infrastructure.groq_llm import GroqLLMClient
from backend.app.infrastructure.jina_embedder import JinaEmbedder
from backend.app.infrastructure.qdrant_store import QdrantVectorStore
from backend.app.infrastructure.supabase_query_log_store import (
    SupabaseQueryLogStore,
)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _build_query_log_adapter(settings: Settings) -> SupabaseQueryLogStore | None:
    """None si Supabase no está configurado (dev/local sin credenciales).

    Un único adapter concreto respalda tanto QueryLogStore (save, mejor
    envuelto en el wrapper no-bloqueante) como QueryLogFinder
    (find_by_share_token, que necesita propagar errores tal cual) — misma
    tabla, mismo cliente HTTP. Lo que se separa son los ports que cada
    consumidor ve, no la implementación.
    """
    if not (settings.supabase_url and settings.supabase_key):
        return None
    return SupabaseQueryLogStore(
        url=settings.supabase_url,
        api_key=settings.supabase_key,
        table=settings.supabase_queries_table,
    )


def _build_query_log_store(settings: Settings) -> QueryLogStore | None:
    """Persistencia del log de consultas, o None si Supabase no está configurado.

    Sin credenciales (dev/local) la feature queda inerte: el use case no guarda
    nada. Con credenciales, envolvemos el adapter en el wrapper no-bloqueante.
    """
    adapter = _build_query_log_adapter(settings)
    if adapter is None:
        return None
    return BackgroundQueryLogStore(adapter)


@lru_cache
def get_use_case() -> QueryUseCase:
    settings = get_settings()
    return QueryUseCase(
        embedder=JinaEmbedder(
            api_key=settings.jina_api_key,
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
        ),
        store=QdrantVectorStore(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            collection=settings.qdrant_collection,
        ),
        llm=GroqLLMClient(
            api_key=settings.groq_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        ),
        top_k=settings.top_k,
        query_log_store=_build_query_log_store(settings),
    )


_SHARES_UNAVAILABLE_DETAIL = "Compartir no está disponible en este momento."


@lru_cache
def get_query_log_finder() -> QueryLogFinder:
    adapter = _build_query_log_adapter(get_settings())
    if adapter is None:
        raise HTTPException(status_code=503, detail=_SHARES_UNAVAILABLE_DETAIL)
    return adapter


@lru_cache
def get_shared_query_use_case() -> GetSharedQueryUseCase:
    return GetSharedQueryUseCase(finder=get_query_log_finder())
