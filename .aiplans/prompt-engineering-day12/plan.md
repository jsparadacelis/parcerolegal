# Task: Prompt Engineering (Day 12)

## Objetivo
Probar 20 queries representativas contra el pipeline RAG en producción (post-migración a
Jina), evaluar calidad de respuestas, formato de citas y detección de out_of_scope. Iterar
el system prompt en `query_use_case.py` si se detectan alucinaciones, citas mal formateadas,
o falsos positivos/negativos de out_of_scope.

## Queries de prueba
15 dentro de alcance (Constitución + sentencias del corpus) + 5 fuera de alcance, cubriendo:
- Derechos fundamentales (salud, vida, igualdad, debido proceso, habeas corpus, tutela)
- Estructura del Estado (poderes, funciones)
- Sentencias específicas del corpus (T-760, C-355, SU-214, T-025, C-239, etc.)
- Preguntas ambiguas o mal formuladas
- Preguntas claramente fuera de alcance (recetas, deportes, programación)

## Output
- `results.md` con cada query, respuesta, fuentes citadas, score más alto, y veredicto
  (✅ buena / ⚠️ mejorable / ❌ problema)
- Cambios al system prompt si aplica, documentados en `implementation_log.md`

## Verificación
- Re-correr las queries problemáticas tras cualquier cambio de prompt
- Confirmar que los tests existentes (`backend/tests/`) sigan pasando
