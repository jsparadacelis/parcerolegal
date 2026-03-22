# Task: chunk_documents.py (TDD)

## Objetivo
Dividir los JSONs procesados (constitución + sentencias) en chunks de 800-1000 chars con 150 chars de overlap, cortando en límites de oración. Output: `data/processed/chunks.json` listo para embedding y upload a Qdrant.

## Estrategia de chunking
- **Constitución**: chunk por artículo. Artículos cortos (<1000 chars) = 1 chunk. Artículos largos se splitean con overlap.
- **Sentencias**: chunk por sección (antecedentes, consideraciones, resuelve). Secciones vacías se omiten.
- **Mínimo**: fragmentos <200 chars se fusionan con el chunk anterior (no aplica a artículos completos cortos).
- **Sentence boundaries**: regex `(?<=[.!?])\s+(?=[A-Z])` para cortar en oraciones.

## Chunk schema
```json
{
  "chunk_id": "constitucion_art_1_0",
  "text": "...",
  "source_type": "constitucion",
  // constitucion fields: article_numero, titulo, capitulo, url_original
  // sentencia fields: sentencia_id, tipo, year, tema, seccion, source_url
}
```

## Funciones
- `split_text(text, chunk_max=1000, chunk_min=800, overlap=150, min_chunk_len=200)` → list[str]
- `chunk_constitucion(path)` → list[dict]
- `chunk_sentencia(path)` → list[dict]
- `chunk_all_sentencias(dir)` → list[dict]
- `build_output(const_chunks, sent_chunks)` → dict
- `main()` → orquesta todo, escribe chunks.json

## Tests: 26 tests cubriendo split_text, chunk_constitucion, chunk_sentencia, build_output, main
