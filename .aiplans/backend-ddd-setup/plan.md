# Task: backend-ddd-setup

## Objetivo
Montar el esqueleto del backend FastAPI siguiendo arquitectura DDD en 4 capas: domain, application, infrastructure, api. El backend debe tener estructura lista para conectar Qdrant, Groq y exponer `POST /api/query`.

## Capas
- **domain/**: entities.py (RetrievedChunk, Source, QueryResult), ports.py (Embedder, VectorStore, LLMClient), services.py (filter_by_score, is_out_of_scope)
- **application/**: query_use_case.py (QueryUseCase — orquesta embedder + store + llm)
- **infrastructure/**: config.py (Settings con pydantic-settings), groq_llm.py (stub), qdrant_store.py (stub), st_embedder.py (stub)
- **api/**: main.py (FastAPI app), routes.py (GET /api/health, POST /api/query stub), schemas.py (QueryRequest, QueryResponse), dependencies.py (Depends factories)

## Output spec
- `uvicorn backend.app.api.main:app` arranca sin errores
- `GET /api/health` → `{"status": "ok"}`
- 24 tests pasando

## Tests
- domain/test_entities.py — construcción e inmutabilidad de dataclasses
- domain/test_services.py — filter_by_score, is_out_of_scope
- application/test_query_use_case.py — construcción con Fakes, NotImplementedError stub
- api/test_routes.py — health check, query endpoint (stub)
