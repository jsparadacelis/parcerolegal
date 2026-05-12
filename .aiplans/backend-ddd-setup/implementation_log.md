# Implementation Log: backend-ddd-setup

## Status: Complete

---

## Log

### 2026-03-22 — Implementación completada (TDD)
- Arquitectura DDD 4 capas creada desde cero
- 24 tests pasando: 15 domain + 2 application + 7 api (integration con TestClient)

#### Estructura final
```
backend/app/
├── domain/
│   ├── entities.py       # RetrievedChunk, Source, QueryResult (frozen dataclasses)
│   ├── ports.py          # Embedder, VectorStore, LLMClient (Protocol)
│   └── services.py       # filter_by_score, is_out_of_scope
├── application/
│   └── query_use_case.py # QueryUseCase — stub, lanza NotImplementedError
├── infrastructure/
│   ├── config.py         # Settings (pydantic-settings, .env)
│   ├── groq_llm.py       # GroqLLMClient — stub
│   ├── qdrant_store.py   # QdrantVectorStore — stub
│   └── st_embedder.py    # STEmbedder — stub
└── api/
    ├── main.py           # FastAPI app factory
    ├── routes.py         # /api/health + /api/query (stub 501)
    ├── schemas.py        # QueryRequest, QueryResponse (Pydantic v2)
    └── dependencies.py   # get_settings, get_use_case (Depends)
```

#### Decisiones
1. **Protocol para ports**: Tipado estructural (duck typing) en vez de ABC — más flexible para Fakes en tests
2. **frozen=True en entities**: Inmutabilidad garantizada, hashables
3. **Depends en dependencies.py**: Settings y QueryUseCase se inyectan vía FastAPI Depends, facilita test override
4. **conftest.py con Fakes**: FakeEmbedder, FakeVectorStore, FakeLLMClient — usados en todos los tests de application y api

#### Verificación
- `pytest backend/tests/ -v` → 24/24 passed
- `uvicorn backend.app.api.main:app --port 8000` → arranca sin errores
- `curl localhost:8000/api/health` → `{"status":"ok"}`
