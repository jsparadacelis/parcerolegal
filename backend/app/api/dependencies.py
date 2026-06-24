"""FastAPI dependency injection — wires infrastructure to use cases."""

from __future__ import annotations

from functools import lru_cache

from backend.app.application.query_use_case import QueryUseCase
from backend.app.infrastructure.config import Settings
from backend.app.infrastructure.groq_llm import GroqLLMClient
from backend.app.infrastructure.jina_embedder import JinaEmbedder
from backend.app.infrastructure.qdrant_store import QdrantVectorStore


@lru_cache
def get_settings() -> Settings:
    return Settings()


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
    )
