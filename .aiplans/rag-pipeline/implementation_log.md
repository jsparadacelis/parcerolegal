# Implementation Log: rag-pipeline

## Status: Complete

---

## Log

### 2026-05-09 — Plan creado
- Próximo paso tras groq-llm-integration
- Implementar QdrantVectorStore, STEmbedder, QueryUseCase.execute(), POST /api/query
- Al completar: pipeline RAG end-to-end funcional

### 2026-05-09 — Implementación completada (TDD)

- 28 tests escritos primero, luego implementación
- Suite completa: 58/58 tests pasando

#### Archivos implementados

| Archivo | Tests |
|---|---|
| `backend/tests/infrastructure/test_qdrant_store.py` | 8 tests |
| `backend/tests/infrastructure/test_st_embedder.py` | 5 tests |
| `backend/tests/application/test_query_use_case.py` | 11 tests (reemplaza stub) |
| `backend/tests/api/test_routes.py` | 10 tests (reemplaza stub) |

#### Decisiones

1. **QdrantVectorStore no filtra por score**: La infraestructura devuelve los top-k raw de Qdrant. El filtro vive en `domain/services.filter_by_score` y se aplica en QueryUseCase — esto separa correctamente las responsabilidades (infra vs dominio).

2. **`_to_chunk` extrae metadata**: Los campos `text` y `source_type` se mapean directamente a RetrievedChunk; el resto del payload va a `metadata` como dict. Así el store no necesita saber el schema concreto de cada tipo de documento.

3. **`SentenceTransformerEmbedder` carga el modelo en `__init__`**: Carga única en construcción (singleton de instancia), como `GroqLLMClient`. El fixture de tests parchea `SentenceTransformer` antes de construir la instancia.

4. **`_chunk_to_source` como función privada de módulo**: Convierte `RetrievedChunk → Source` separando lógica de constitución vs sentencia. Se puede extender fácilmente para otros `source_type`.

5. **`elapsed_ms` como lambda**: Captura `start` con cierre para evitar duplicar `(time.time() - start) * 1000` en las dos ramas (out_of_scope y normal).

#### Verificación

- `pytest backend/tests/ -v` → 58/58 passed
- Endpoint `POST /api/query` funcional end-to-end con Fakes en tests de integración
