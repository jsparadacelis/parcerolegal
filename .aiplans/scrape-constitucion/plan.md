# Task: Create scrape_constitucion.py (TDD)

## Source
- Notion task: `307444f7-47b3-80fe-91d8-f1d44d87a2c4`
- Related: `307444f7-47b3-80d1-aa57-d8afc3e4db2c` (Save constitucion.json)
- Database: Day 1-2 Constitución Scraping (`collection://307444f7-47b3-803d-8130-000b7764092a`)
- Priority: High | Estimate: 3h

## Objetivo
Scraper TDD que descarga la Constitución Política de Colombia (1991) desde funcionpublica.gov.co y genera `data/processed/constitucion.json` con artículos estructurados listos para vectorización en Qdrant.

## Decisiones
- **Fuente:** `https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4125`
- **Transitorios:** excluidos (solo artículos permanentes)
- **Metodología:** TDD — 19 tests primero, implementación mínima
- **Dependencias:** separadas en `data/requirements.txt` (no en backend/)
- **Tests:** en `data/tests/scripts/` (espejo de `data/scripts/`)

## Output
- `data/processed/constitucion.json` — JSON estructurado (metadata + articles)
- `data/raw/constitucion.html` — HTML crudo para referencia

## JSON Schema
```json
{
  "metadata": {
    "title": "Constitución Política de Colombia 1991",
    "source_url": "<url>",
    "scraped_at": "<ISO timestamp>",
    "total_articles": 380
  },
  "articles": [
    {
      "id": "art_1",
      "numero": 1,
      "titulo": "TITULO I.",
      "capitulo": null,
      "texto": "Colombia es un Estado social de derecho...",
      "url_original": "<url>#1"
    }
  ]
}
```

## Archivos

| Archivo | Propósito |
|---------|-----------|
| `data/requirements.txt` | httpx, bs4, lxml, pytest, pytest-httpx |
| `data/__init__.py` | Package marker |
| `data/tests/scripts/__init__.py` | Package marker |
| `data/tests/scripts/fixtures/constitucion_sample.html` | Fragmento real (2 títulos, 6 arts, transitorios) |
| `data/tests/scripts/test_scrape_constitucion.py` | 19 unit tests |
| `data/scripts/scrape_constitucion.py` | fetch_page, parse_articles, build_metadata, main |
| `conftest.py` (raíz) | sys.path para imports |

## Funciones públicas
- `fetch_page(url, raw_path)` → GET + guarda HTML + retorna string
- `parse_articles(html, source_url)` → lista de dicts (excluye transitorios)
- `build_metadata(articles, source_url)` → dict con title, source_url, scraped_at, total_articles
- `main()` → orquesta fetch → parse → build_metadata → JSON

## Verificación
```bash
pytest data/tests/scripts/test_scrape_constitucion.py -v  # 19/19 passed
python data/scripts/scrape_constitucion.py                # integration (red real)
python -m json.tool data/processed/constitucion.json      # validar JSON
```
