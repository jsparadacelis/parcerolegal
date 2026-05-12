# Task: embed_and_upload.py (TDD)

## Objetivo
Generar embeddings de los 7,345 chunks en `chunks.json` usando sentence-transformers y subirlos a Qdrant Cloud en batches. Output: colección `parcerolegal` con 7,340 puntos listos para búsqueda semántica.

## Modelo
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` — 384 dimensiones, multilingüe, corre en CPU.

## Estrategia
- Cargar `chunks.json` completo en memoria
- Generar embeddings en batch (sentence-transformers)
- Subir a Qdrant en batches de 100 puntos con metadata completa
- Verificar con 5 queries de prueba post-upload

## Qdrant schema
- Collection: `parcerolegal`
- Vector size: 384
- Distance: Cosine
- Payload: chunk_id, text, source_type + metadata específica por tipo

## Funciones
- `load_chunks(path)` → list[dict]
- `embed_texts(texts, model_name)` → list[list[float]]
- `upload_to_qdrant(client, collection, chunks, embeddings)` → int (puntos subidos)
- `main()` → orquesta todo

## Tests: 10 tests cubriendo carga, embedding, upload (mocked Qdrant), main
