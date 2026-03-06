# Implementation Log: scrape_constitucion.py

## Status: Done

---

## Log

### 2026-02-14 — Scaffold inicial
- Estructura de directorios, requirements.txt, .gitignore
- Primera versión del scraper (sin tests)
- Notion task → In progress

### 2026-03-05 — Rewrite TDD completo
- Analicé el HTML real de funcionpublica.gov.co para entender la estructura del DOM
  - Contenido en `<div class="descripcion-contenido">`
  - Artículos: `<p><strong>ARTÍCULO<a id="sp1" name="1"></a> 1.</strong> texto...</p>`
  - Títulos/capítulos: `<p align="center"><strong>TITULO I.</strong></p>`
  - Párrafos de continuación como `<p>` hermanos sin prefijo ARTÍCULO
  - Jurisprudencia en botones y divs ocultos → se filtran
  - Referencias `(Ver Ley...)` → se filtran
- Creé fixture HTML realista con 6 artículos + 2 transitorios
- Escribí 19 tests cubriendo: campos requeridos, formato id, no HTML en texto, exclusión de transitorios, tracking de título/capítulo, multi-párrafo, metadata
- Implementación mínima para pasar los tests
- Refactored: eliminé función anidada `flush()` con `nonlocal` → `_save_article()` a nivel módulo
- Renombré variables: `raw`→`text`, `strong`→`bold_text`, `match`→`article_match`
- **19/19 tests passing**

### Decisiones notables
- `data/requirements.txt` separado de `backend/requirements.txt` — el pipeline es independiente
- Tests en `data/tests/scripts/` (no dentro de `data/scripts/tests/`) — tests como hermano de scripts
- Convenciones Python guardadas como skill en `.claude/skills/python-conventions/`

### 2026-03-06 — Integration test + fix títulos

- Integration test contra página real: 383 artículos extraídos
- Descubierto que el HTML de funcionpublica.gov.co no incluye encabezados de Títulos I-XI (solo XII y XIII existen como `<p><strong>`)
- Fix: mapa estático `_STRUCTURE_MAP` con los 13 títulos y ~30 capítulos de la Constitución, aplicado como post-procesamiento en `parse_articles()`
- Resultado: 0 artículos sin título, 17 sin capítulo (correcto: Títulos I y XIII no tienen capítulos)
- 19/19 unit tests passing
- JSON válido, conteo correcto (383 arts, rango art_1 a art_380)
