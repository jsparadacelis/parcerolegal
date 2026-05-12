# Task: rag-pipeline (Day 10)

## Objetivo
Implementar el pipeline RAG completo: `QdrantVectorStore`, `STEmbedder`, `QueryUseCase.execute()`, y el endpoint `POST /api/query`. Al terminar, una pregunta en español debe devolver una respuesta con fuentes desde Qdrant + Groq.

## Componentes a implementar

### 1. `infrastructure/qdrant_store.py` — QdrantVectorStore
Adaptador del puerto `VectorStore`. Busca los top-k chunks más similares en Qdrant.
- `search(embedding, top_k=5)` → list[RetrievedChunk]
- Filtra por score mínimo (similarity_threshold desde Settings)
- Mapea payload de Qdrant a RetrievedChunk

### 2. `infrastructure/st_embedder.py` — STEmbedder
Adaptador del puerto `Embedder`. Genera embeddings con sentence-transformers.
- `embed(text)` → list[float]
- Modelo: `paraphrase-multilingual-MiniLM-L12-v2` (384 dims)
- Carga el modelo una sola vez (singleton en instancia)

### 3. `application/query_use_case.py` — QueryUseCase.execute()
Orquesta el pipeline completo:
1. Embed la pregunta
2. Buscar top-5 chunks en Qdrant
3. Si no hay chunks con score ≥ 0.65 → retornar out_of_scope=True
4. Construir prompt con chunks como contexto
5. Llamar al LLM → obtener respuesta
6. Construir y retornar QueryResult con sources

### 4. `api/routes.py` — POST /api/query
Conectar el endpoint al QueryUseCase real (quitar stub 501).
- Request: `QueryRequest(question: str)`
- Response: `QueryResponse(answer, sources, out_of_scope, processing_time_ms)`

## System prompt template
```
Eres un asistente jurídico colombiano. Responde en español claro y preciso.
Basa tu respuesta ÚNICAMENTE en los siguientes fragmentos de la legislación colombiana:

{contexto}

Pregunta: {pregunta}

Respuesta:
```

## Output spec
- `POST /api/query {"question": "¿Qué es el habeas corpus?"}` → respuesta con sources y processing_time_ms
- Out-of-scope: si ningún chunk ≥ 0.65 → `{"answer": "...", "sources": [], "out_of_scope": true}`
- Tests: ~15 tests nuevos cubriendo QdrantVectorStore, STEmbedder, QueryUseCase.execute(), y el endpoint completo

## Orden de implementación
1. Tests de QdrantVectorStore (mock qdrant-client)
2. Implementar QdrantVectorStore
3. Tests de STEmbedder (mock sentence-transformers)
4. Implementar STEmbedder
5. Tests de QueryUseCase.execute() con Fakes
6. Implementar QueryUseCase.execute()
7. Tests de integración del endpoint POST /api/query
8. Conectar endpoint
