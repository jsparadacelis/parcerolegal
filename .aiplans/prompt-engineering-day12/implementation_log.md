# Implementation log — prompt-engineering-day12

- 2026-06-24: Corridas 20 queries (15 dentro de alcance, 5 fuera) contra producción
  post-migración a Jina. Ver `results.md` para detalle por query.
  - System prompt actual (en `query_use_case.py`) funciona bien: sin alucinaciones,
    citas correctas, out-of-scope detection 5/5 en queries irrelevantes. No se hicieron
    cambios al prompt.
  - Gap encontrado: queries que nombran una sentencia directamente
    ("¿qué dice la sentencia T-760 de 2008?") fallan en retrieval — el embedding de la
    pregunta no se parece al contenido del chunk, solo a la cita. Scores 0.36-0.49,
    por debajo o apenas sobre el umbral 0.45. No es un problema del prompt ni del
    umbral; es una limitación de la búsqueda puramente semántica.
  - Recomendación para una iteración futura: agregar filtro de metadata en
    `QdrantVectorStore.search` (filtro por `sentencia_id` cuando la pregunta matchea un
    patrón regex de cita) — no implementado aquí, requiere diseño de la capa de
    retrieval. Pendiente de decisión del usuario sobre prioridad.
- 2026-06-24: Usuario pidió implementar el fix de inmediato. Agregado
  `extract_sentencia_id()` en `domain/services.py` (regex para T-/C-/SU- + número +
  año, soporta "T-760 de 2008", "T-760-08", "T-760/08"). `QdrantVectorStore.search`
  acepta `sentencia_id` opcional y construye un filtro de payload exacto. Cuando hay
  match por ID, se salta el umbral de similitud (`SIMILARITY_THRESHOLD`) — el match
  exacto de ID es una señal de relevancia más fuerte que el coseno para este tipo de
  queries. TDD completo (services, qdrant_store, query_use_case, conftest). Suite:
  158 tests pasando. Commit `39c0bc2`, pusheado y redesplegado.
  Bug encontrado en el primer redeploy: Qdrant devolvía 400 ("Index required but not
  found for sentencia_id") porque el filtro por payload requiere un índice explícito
  en Qdrant Cloud. Resuelto creando el índice `keyword` sobre `sentencia_id` vía
  `PUT /collections/parcerolegal/index`. Verificado en producción: ambas queries
  problemáticas (T-760, SU-214) ahora devuelven la sentencia correcta con
  `out_of_scope: false`; las queries fuera de alcance siguen detectándose bien.
