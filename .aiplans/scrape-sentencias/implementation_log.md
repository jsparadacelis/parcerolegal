# Implementation Log: scrape_sentencias.py

## Status: Complete

---

## Log

### 2026-03-07 — Plan creado
- Análisis de HTML de 4 sentencias (T-760-08, C-355-06, SU-214-16, T-025-04, T-406-93)
- Estructura identificada: `<div class="Section1">`, clases MsoNormal, secciones por headings/bold
- Plan con 15 tests, 5 funciones públicas, JSON por sentencia

### 2026-03-22 — Implementación completada (TDD)
- **Tests escritos primero**: 25 tests en `data/tests/scripts/test_scrape_sentencias.py`
- **Fixture creado**: `sentencia_sample.html` — HTML realista compacto
- **Implementación**: `data/scripts/scrape_sentencias.py` con todas las funciones del plan

#### Decisiones durante implementación
1. **Encoding windows-1252**: El HTML de la Corte usa windows-1252 pero httpx lo decodifica como UTF-8, produciendo caracteres `U+FFFD`. Solución: decodificar `response.content` con windows-1252 explícitamente.
2. **URL SU-214-16**: La URL con guión (`SU-214-16.htm`) redirige a la nueva SPA Angular de la Corte (sin contenido). La URL correcta es sin guión: `su214-16.htm`.
3. **Caracteres de reemplazo \ufffd**: Además de `\xa0` (NBSP), los HTMLs tienen `\ufffd` por el encoding. Se añadió al regex de limpieza.
4. **Regex de secciones flexibles**: Sentencias antiguas (C-221-94) usan numeración arábiga (`1. ANTECEDENTES`) en vez de romanos (`I. ANTECEDENTES`). Se generalizó el prefijo a `[\dIVXivx]{0,5}`.
5. **Secciones vacías aceptables**: Algunas sentencias (C-221-94 sin RESUELVE, C-355-06 con estructura atípica) no tienen todas las secciones estándar. El `texto_completo` siempre tiene contenido y es lo que usará el chunker.

#### Resultados finales — 10 sentencias scrapeadas
| Sentencia | Magistrado | Texto total |
|-----------|-----------|-------------|
| T-760-08 | Manuel José Cepeda Espinosa | 1.4M chars |
| C-355-06 | (complejo, múltiples ponentes) | 1.7M chars |
| SU-214-16 | Alberto Rojas Ríos | 903K chars |
| T-025-04 | Manuel José Cepeda Espinosa | 451K chars |
| T-406-92 | Ciro Angarita Barón | 81K chars |
| C-221-94 | Carlos Gaviria Díaz | 130K chars |
| C-239-97 | Carlos Gaviria Díaz | 324K chars |
| T-881-02 | Eduardo Montealegre Lynett | 153K chars |
| C-577-11 | Gabriel Eduardo Mendoza Martelo | 855K chars |
| T-398-19 | Alberto Rojas Ríos | 244K chars |

#### Verificación
- `pytest data/tests/ -v` → 44/44 passed (19 constitución + 25 sentencias)
- `python3 data/scripts/scrape_sentencias.py` → 10 JSONs en `data/processed/sentencias/`
- JSONs validados con `json.tool`
