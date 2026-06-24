# Implementation log — migrate-jina-embeddings

- 2026-06-24: Plan aprobado. Modelo elegido: jina-embeddings-v3, dimensions=1024,
  task asimétrico (retrieval.query / retrieval.passage). Usuario va a obtener
  JINA_API_KEY y la ejecución del re-embed en Qdrant Cloud la hace el asistente
  una vez la key esté disponible.
- 2026-06-24: Implementado `JinaEmbedder` (TDD, 6 tests) reemplazando
  `SentenceTransformerEmbedder`/HF Inference API. Actualizados `config.py`,
  `dependencies.py`, `data/scripts/embed_and_upload.py` (ahora embebe vía HTTP a
  Jina con `task=retrieval.passage` por batch en vez de `SentenceTransformer`
  local), tests del pipeline de datos, `data/requirements.txt`, `.env.example` y
  `CLAUDE.md`. Suite completa: 145 tests pasando.
  Pendiente: usuario debe agregar `JINA_API_KEY` a `.env` (también falta
  `GROQ_API_KEY` ahí) antes de correr el re-embed contra Qdrant Cloud
  (producción) y luego actualizar Railway con `JINA_API_KEY`.
- 2026-06-24: Cluster de Qdrant Cloud original estaba pausado/inexistente;
  usuario creó uno nuevo (nueva URL/API key en `.env`). Ejecutado
  `embed_and_upload.py` contra el cluster nuevo. Falló a los 900/7345 puntos
  por rate limit (429) de Jina. Se agregó retry con backoff exponencial
  (`MAX_RETRIES=5`, `BASE_DELAY=5.0`, mismo patrón que `groq_llm.py`) y soporte
  de resume vía `START_BATCH` env var (no recrea la colección si ya existe).
  Reanudado con `START_BATCH=9` — completado: 7340 puntos en Qdrant.
  Verificación de retrieval: separación clara entre queries dentro de alcance
  (scores ~0.55-0.78) y fuera de alcance (~0.11-0.18) con jina-embeddings-v3,
  pero distribución de scores más baja que con granite (0.78-0.85 antes).
  El umbral `SIMILARITY_THRESHOLD` (antes 0.65) causaba falsos `out_of_scope`
  en preguntas legítimas (ej. "habeas corpus" con score 0.547). Recalibrado a
  **0.45** en `backend/app/domain/services.py`, `config.py` y `CLAUDE.md`
  (con margen amplio sobre el ruido fuera de alcance). Tests de
  `test_services.py` actualizados a los nuevos valores límite. Suite completa:
  146 tests pasando.
