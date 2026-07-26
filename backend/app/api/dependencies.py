"""FastAPI dependency injection — wires infrastructure to use cases."""

from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException

from backend.app.application.query_use_case import QueryUseCase
from backend.app.application.share_answer_use_case import ShareAnswerUseCase
from backend.app.domain.ports import QueryLogStore, SharedAnswerFinder, SharedAnswerStore
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
from backend.app.infrastructure.supabase_shared_answer_store import (
    SupabaseSharedAnswerStore,
)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _build_query_log_store(settings: Settings) -> QueryLogStore | None:
    """Persistencia del log de consultas, o None si Supabase no está configurado.

    Sin credenciales (dev/local) la feature queda inerte: el use case no guarda
    nada. Con credenciales, envolvemos el adapter en el wrapper no-bloqueante.
    """
    if not (settings.supabase_url and settings.supabase_key):
        return None
    return BackgroundQueryLogStore(
        SupabaseQueryLogStore(
            url=settings.supabase_url,
            api_key=settings.supabase_key,
            table=settings.supabase_queries_table,
        )
    )


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


def _build_shared_answer_store(settings: Settings) -> SupabaseSharedAnswerStore | None:
    """None si Supabase no está configurado (dev/local sin credenciales).

    Un único adapter concreto respalda tanto SharedAnswerStore (save) como
    SharedAnswerFinder (get) — misma tabla, mismo cliente HTTP. Lo que se
    separa son los ports que cada consumidor ve, no la implementación.
    """
    if not (settings.supabase_url and settings.supabase_key):
        return None
    return SupabaseSharedAnswerStore(
        url=settings.supabase_url,
        api_key=settings.supabase_key,
        table=settings.supabase_shared_answers_table,
    )


_SHARES_UNAVAILABLE_DETAIL = "Compartir no está disponible en este momento."


@lru_cache
def get_shared_answer_store() -> SharedAnswerStore:
    store = _build_shared_answer_store(get_settings())
    if store is None:
        raise HTTPException(status_code=503, detail=_SHARES_UNAVAILABLE_DETAIL)
    return store


@lru_cache
def get_shared_answer_finder() -> SharedAnswerFinder:
    store = _build_shared_answer_store(get_settings())
    if store is None:
        raise HTTPException(status_code=503, detail=_SHARES_UNAVAILABLE_DETAIL)
    return store


@lru_cache
def get_share_use_case() -> ShareAnswerUseCase:
    return ShareAnswerUseCase(query_use_case=get_use_case(), store=get_shared_answer_store())
