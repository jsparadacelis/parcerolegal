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
