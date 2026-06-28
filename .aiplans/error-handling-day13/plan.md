# Day 13 — Error Handling

## Objetivo
Hacer el backend más robusto con timeout handling, validación de input mejorada,
schemas de error consistentes, y request logging.

## Alcance

### 1. Timeout handling
- `groq_llm.py`: `timeout=40` en `requests.post()`
- `jina_embedder.py`: `timeout=10` en `requests.post()`
- `main.py`: exception handler `requests.exceptions.Timeout` → HTTP 503

### 2. Input validation
- `schemas.py`: field_validator `mode='before'` que hace `.strip()` a `question`
  antes de que corra `min_length=3`, para que `"   "` (3 espacios) sea rechazado

### 3. Error response schemas
- `schemas.py`: `ErrorResponse(detail: str)` — body consistente en 503/500
- `main.py`: exception handler para `Exception` genérica → 500

### 4. Request logging
- `main.py`: middleware HTTP que loguea cada request (método, path, status, ms)
- `routes.py`: log de negocio por query (question length, out_of_scope, elapsed_ms)
- Logger name: `"parcerolegal"`

## Verificación
- Todos los tests existentes siguen pasando
- Nuevos tests cubren: timeout→503, whitespace→422, log entry presente
