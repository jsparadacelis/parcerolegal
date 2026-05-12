# Implementation Log: embed_and_upload.py

## Status: Complete

---

## Log

### 2026-03-22 — Implementación completada (TDD)
- 10 tests escritos primero, todos pasan
- Modelo: `paraphrase-multilingual-MiniLM-L12-v2` (384 dims)
- 7,345 embeddings generados en ~9 min en CPU
- Upload a Qdrant en batches de 100 → 7,340 puntos (5 duplicados omitidos)

#### Decisiones
1. **Batch size 100**: Balance entre velocidad y memoria; Qdrant acepta hasta 1000 pero 100 es más estable
2. **7,340 vs 7,345**: 5 chunks con chunk_id duplicado fueron descartados por Qdrant (upsert silencioso)

#### Verificación post-upload — test_queries.py
| Query | Score top-1 |
|-------|------------|
| ¿Qué derechos fundamentales garantiza la Constitución? | 0.85 |
| ¿Cuál es el derecho a la salud en Colombia? | 0.83 |
| ¿Qué dice la Constitución sobre el aborto? | 0.81 |
| ¿Qué es el estado de emergencia? | 0.79 |
| ¿Qué protege el habeas corpus? | 0.78 |

Todos muy por encima del threshold de 0.65 → retrieval excelente.

#### Verificación
- `pytest data/tests/ -v` → 70/70 passed
- `python3 data/scripts/embed_and_upload.py` → 7,340 puntos en Qdrant
