# Task: groq-llm-integration

## Objetivo
Implementar `GroqLLMClient` en `backend/app/infrastructure/groq_llm.py` como adaptador real del puerto `LLMClient`. Debe llamar a la API de Groq con Llama 3.1 70B, manejar rate limits con retry exponencial, y levantar errores apropiados.

## Comportamiento esperado
- `generate(prompt)` → string con la respuesta del LLM
- Modelo: `llama-3.1-70b-versatile`, temperature=0, max_tokens=1024
- Rate limit: retry hasta 3 veces con backoff exponencial (1s → 2s → 4s)
- Otros errores API: propagan inmediatamente sin retry
- Respuesta vacía: lanza `ValueError`

## Tests (TDD — 7 tests)
- Happy path: retorna contenido de la API
- Parámetros correctos enviados a Groq
- Retry exitoso tras RateLimitError
- Raises tras max retries
- Error no-rate-limit propaga inmediatamente
- Respuesta vacía lanza ValueError
- Backoff exponencial verificado (segundo delay > primero)
