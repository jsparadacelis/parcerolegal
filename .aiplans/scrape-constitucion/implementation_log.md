# Implementation Log: scrape_constitucion.py

## Status: Done (unit tests) | Pendiente: integration test con red real

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

### Pendiente
- [ ] Correr integration test contra la página real (`python data/scripts/scrape_constitucion.py`)
- [ ] Validar que el conteo de artículos sea ~380
- [ ] Marcar tareas Notion como Done tras integration test exitoso
