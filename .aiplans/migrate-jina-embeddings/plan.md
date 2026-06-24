# Migrar embeddings de HF Inference API (granite-97m) a Jina AI (jina-embeddings-v3)

## Contexto
El embedder actual (`backend/app/infrastructure/st_embedder.py`) llama a la HF Inference API
con el modelo `ibm-granite/granite-embedding-97m-multilingual-r2`. Esa API ha demostrado ser
inestable en producción (el modelo dejó de estar disponible sin aviso, ver Notion bug tracker,
nota del 2026-06-02). Además existe una inconsistencia ya presente: el script de carga inicial
(`data/scripts/embed_and_upload.py`) generó los 7345 vectores en Qdrant usando
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` corriendo localmente — un modelo
**distinto** al que usa el embedder de runtime (granite). Como ambos producen 384 dimensiones,
no hay error técnico, pero las queries y los documentos viven en espacios vectoriales diferentes,
degradando el retrieval. Esta migración a Jina resuelve ambos problemas a la vez: un único
proveedor estable vía HTTP, y el mismo modelo para indexar el corpus y para embeber las queries.

Se usará `jina-embeddings-v3` (multilingüe, soporta `task` asimétrico: `retrieval.passage` para
indexar el corpus, `retrieval.query` para las preguntas del usuario — mejora la calidad de
retrieval en RAG), con `dimensions=1024`.

## Cambios de código

### 1. Backend — nuevo embedder
- Crear `backend/app/infrastructure/jina_embedder.py` con clase `JinaEmbedder`, reemplazando
  `st_embedder.py` (se elimina, no se mantiene compatibilidad hacia atrás).
  - Endpoint: `POST https://api.jina.ai/v1/embeddings`
  - Headers: `Authorization: Bearer {api_key}`, `Content-Type: application/json`
  - Body: `{"model": "jina-embeddings-v3", "task": "retrieval.query", "dimensions": 1024, "input": [text]}`
  - Sigue el patrón de `groq_llm.py` / `qdrant_store.py` (HTTP directo con `requests`, sin SDK)
  - `embed(text) -> list[float]` extrae `response.json()["data"][0]["embedding"]`
- Reemplazar `backend/tests/infrastructure/test_st_embedder.py` por
  `test_jina_embedder.py` (mismo estilo TDD con `responses.RequestsMock`, mockeando la URL y
  verificando body/headers/task type).

### 2. Backend — config y wiring
- `backend/app/infrastructure/config.py`: quitar `hf_token`, agregar `jina_api_key: str = ""`;
  cambiar default de `embedding_model` a `"jina-embeddings-v3"`; agregar
  `embedding_dimensions: int = 1024`.
- `backend/app/api/dependencies.py`: importar y wirear `JinaEmbedder` en vez de
  `SentenceTransformerEmbedder`.

### 3. Pipeline de datos — re-embed script
- `data/scripts/embed_and_upload.py`: reemplazar `SentenceTransformer` por llamadas HTTP a Jina
  (`task="retrieval.passage"`, `dimensions=1024`, batching de textos en el body `input` —
  Jina acepta listas, así que se puede mantener `BATCH_SIZE=100` pero ahora como llamadas HTTP
  por batch en lugar de inferencia local). Mantener `qdrant_client` SDK aquí (script
  administrativo, no corre en Railway, no es el cuello de botella de OOM) salvo por
  `VECTOR_SIZE` que pasa de 384 a 1024.
- `data/tests/scripts/test_embed_and_upload.py`: actualizar `TestGenerateEmbeddings` para
  mockear la llamada HTTP a Jina en vez de `SentenceTransformer`; actualizar tests de
  `create_collection`/`upload_batch` que asumen 384 dims a 1024.

### 4. Dependencias y env
- `data/requirements.txt`: quitar `sentence-transformers`, agregar `requests`.
- `.env` / `.env.example`: quitar referencias a `HF_TOKEN` si existieran, agregar
  `JINA_API_KEY=your_jina_api_key`.
- `CLAUDE.md`: actualizar la fila de "Embeddings" en la tabla de Tech Stack a
  `jina-embeddings-v3 (Jina AI)`.

### 5. `.aiplans/`
- Crear `.aiplans/migrate-jina-embeddings/plan.md` (este plan) e
  `implementation_log.md` con el avance.

## Pasos de ejecución (en orden)
1. Implementar `JinaEmbedder` + tests (TDD: tests primero, ver skill `python-tdd`).
2. Actualizar `config.py` y `dependencies.py`.
3. Actualizar `embed_and_upload.py` + sus tests.
4. Actualizar requirements, `.env.example`, `CLAUDE.md`.
5. Correr toda la suite (`pytest backend/tests/ data/tests/ -v`) — debe quedar verde.
6. Una vez el usuario confirme que `JINA_API_KEY` está en `.env`: ejecutar
   `python data/scripts/embed_and_upload.py` para recrear la colección `parcerolegal` en Qdrant
   Cloud con los 7345 chunks re-embebidos (esto borra los vectores actuales — acción confirmada
   por el usuario).
7. Avisar al usuario que debe actualizar `JINA_API_KEY` en las variables de entorno de Railway
   (no se puede hacer desde aquí) y quitar `HF_TOKEN` si ya no se usa.

## Verificación
- Tests unitarios pasando (backend + data pipeline).
- Tras el re-embed, correr `data/scripts/test_queries.py` (o equivalente) contra Qdrant para
  confirmar scores de similitud razonables (>0.65) con las nuevas queries embebidas vía Jina.
- Smoke test local: `uvicorn backend.app.main:app --reload` + `POST /api/query` con una pregunta
  real, confirmar que devuelve respuesta con fuentes (no `out_of_scope`).
