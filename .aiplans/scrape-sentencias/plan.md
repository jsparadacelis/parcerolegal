# Task: Create scrape_sentencias.py (TDD)

## Source
- Notion board: Day 3-4: Sentencias Scraping
- Priority: High | Estimate: 4h (scraper) + 4h (scraping runs) + 2h (sections) + 1h (validation)

## Objetivo
Scraper TDD que descarga sentencias clave de la Corte Constitucional desde corteconstitucional.gov.co/relatoria/ y genera archivos JSON individuales en `data/processed/sentencias/` con secciones estructuradas listas para chunking y vectorización.

## Análisis del HTML fuente
- **URL pattern:** `https://www.corteconstitucional.gov.co/relatoria/{año}/{tipo}-{numero}-{año_corto}.htm`
- **Container principal:** `<div class="Section1">` (HTML generado desde Word)
- **Clases CSS:** `MsoNormal`, `MsoBodyText`, `MsoCaption` (estilo Word)
- **Secciones:** Identificables por texto en bold/headings: "ANTECEDENTES", "CONSIDERACIONES", "RESUELVE"
- **Metadata en texto:** fecha, magistrado ponente, expediente
- **RTF disponible:** cada página tiene link a .rtf, pero el texto completo está en el HTML

## Sentencias MVP (10 primeras)

### Batch 1 (5 sentencias)
| Sentencia | Año | Tema |
|-----------|-----|------|
| T-760-08 | 2008 | Derecho a la salud |
| C-355-06 | 2006 | Despenalización parcial aborto |
| SU-214-16 | 2016 | Matrimonio igualitario |
| T-025-04 | 2004 | Desplazamiento forzado |
| T-406-92 | 1992 | Estado social de derecho |

### Batch 2 (5 sentencias)
| Sentencia | Año | Tema |
|-----------|-----|------|
| C-221-94 | 1994 | Dosis personal |
| C-239-97 | 1997 | Eutanasia |
| T-881-02 | 2002 | Dignidad humana |
| C-577-11 | 2011 | Parejas del mismo sexo |
| T-398-19 | 2019 | Libertad de expresión |

## Decisiones de diseño
- **Un JSON por sentencia** (no un solo archivo como la Constitución) — cada sentencia es un documento independiente
- **Secciones estructuradas:** extraer hechos/antecedentes, consideraciones, y resuelve como campos separados
- **Texto completo también:** guardar el texto completo para chunking flexible
- **Metodología:** TDD — tests primero, implementación mínima
- **URL config:** lista de sentencias como constante en el módulo (fácil de extender a 25)

## JSON Schema (por sentencia)
```json
{
  "metadata": {
    "sentencia_id": "T-760-08",
    "tipo": "T",
    "numero": "760",
    "year": 2008,
    "fecha": "31 de julio de 2008",
    "magistrado_ponente": "Manuel José Cepeda Espinosa",
    "tema": "Derecho a la salud",
    "source_url": "https://...",
    "scraped_at": "<ISO timestamp>"
  },
  "secciones": {
    "antecedentes": "texto...",
    "consideraciones": "texto...",
    "resuelve": "texto..."
  },
  "texto_completo": "todo el texto de la sentencia..."
}
```

## Archivos

| Archivo | Propósito |
|---------|-----------|
| `data/tests/scripts/fixtures/sentencia_sample.html` | Fragmento HTML realista de una sentencia |
| `data/tests/scripts/test_scrape_sentencias.py` | Unit tests |
| `data/scripts/scrape_sentencias.py` | fetch_sentencia, parse_sentencia, extract_sections, main |

## Funciones públicas
- `SENTENCIAS_LIST` — lista de dicts con id, url, tema para cada sentencia
- `fetch_sentencia(url, raw_path)` → GET + guarda HTML + retorna string
- `parse_metadata(html, sentencia_id, source_url)` → dict con metadata extraída del HTML
- `extract_sections(html)` → dict con antecedentes, consideraciones, resuelve
- `clean_text(html)` → texto limpio sin tags HTML ni artifacts de Word
- `main(sentencias=None)` → orquesta: para cada sentencia, fetch → parse → save JSON

## Tests plan
1. `test_parse_metadata_returns_required_fields`
2. `test_parse_metadata_extracts_magistrado`
3. `test_parse_metadata_extracts_fecha`
4. `test_extract_sections_returns_dict_with_keys`
5. `test_extract_sections_antecedentes_not_empty`
6. `test_extract_sections_consideraciones_not_empty`
7. `test_extract_sections_resuelve_not_empty`
8. `test_clean_text_removes_html_tags`
9. `test_clean_text_removes_mso_artifacts`
10. `test_clean_text_normalizes_whitespace`
11. `test_texto_completo_not_empty`
12. `test_output_json_schema_valid`
13. `test_sentencias_list_has_required_fields`
14. `test_fetch_sentencia_saves_html` (mocked)
15. `test_fetch_sentencia_raises_on_error` (mocked)

## Verificación
```bash
pytest data/tests/scripts/test_scrape_sentencias.py -v  # all tests passed
python data/scripts/scrape_sentencias.py --id T-760-08   # single sentencia test
python data/scripts/scrape_sentencias.py                 # all 10
ls data/processed/sentencias/                            # 10 JSON files
python -m json.tool data/processed/sentencias/T-760-08.json  # validate
```

## Riesgos
- Algunas sentencias pueden tener estructura HTML diferente (más antiguas vs recientes)
- Sentencias muy largas (T-760-08 es enorme) — el texto completo puede ser muy grande
- Algunas sentencias podrían tener el contenido solo en RTF, no en HTML
- Rate limiting del servidor de la Corte
