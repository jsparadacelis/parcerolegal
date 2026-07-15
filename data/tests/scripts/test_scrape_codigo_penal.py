import re
from datetime import datetime
from pathlib import Path

import pytest

from data.scripts.scrape_codigo_penal import (
    build_metadata,
    fetch_page,
    parse_articles,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_HTML = (FIXTURES_DIR / "codigo_penal_sample.html").read_text(encoding="utf-8")
SOURCE_URL = "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=6388"


@pytest.fixture
def articles():
    return parse_articles(SAMPLE_HTML, SOURCE_URL)


# ---------------------------------------------------------------------------
# parse_articles — general shape
# ---------------------------------------------------------------------------


def test_parse_articles_returns_list(articles):
    assert isinstance(articles, list)
    assert len(articles) > 0


def test_article_has_required_fields(articles):
    required = {"id", "numero", "nombre", "libro", "titulo", "capitulo", "texto", "url_original"}
    for art in articles:
        missing = required - art.keys()
        assert not missing, f"Artículo {art.get('id')} le faltan campos: {missing}"


def test_article_id_format(articles):
    """El id sigue el patrón 'cp_art_<numero>[_sufijo]' (ej: 'cp_art_101',
    'cp_art_103_a', 'cp_art_269_1'). El sufijo puede ser letra o número — la Ley
    599/2000 usa ambos ("243-A" y "269-1")."""
    pattern = re.compile(r"^cp_art_\d+(_[a-z0-9]+)?$")
    for art in articles:
        assert pattern.match(art["id"]), (
            f"id inválido: '{art['id']}' — debe seguir el patrón cp_art_<número>[_sufijo]"
        )


def test_article_numero_is_positive_int(articles):
    for art in articles:
        assert isinstance(art["numero"], int), f"numero debe ser int, got {type(art['numero'])}"
        assert art["numero"] > 0


def test_article_texto_no_html_tags(articles):
    for art in articles:
        assert "<" not in art["texto"], f"cp_art_{art['numero']}: texto contiene '<'"
        assert ">" not in art["texto"], f"cp_art_{art['numero']}: texto contiene '>'"


def test_article_texto_is_nonempty(articles):
    for art in articles:
        assert art["texto"].strip(), f"cp_art_{art['numero']}: texto está vacío"


def test_article_url_original_contains_source(articles):
    base = "funcionpublica.gov.co"
    for art in articles:
        assert base in art["url_original"], (
            f"cp_art_{art['numero']}: url_original no contiene el dominio"
        )


# ---------------------------------------------------------------------------
# Scope: solo Libro II (Parte Especial)
# ---------------------------------------------------------------------------


def test_only_libro_ii_articles_are_included(articles):
    """Decisión 2026-07-15: solo Libro II. El fixture incluye Arts. 1 y 27 (Libro I,
    deben excluirse) y Arts. 101, 103, 239 (Libro II, deben incluirse)."""
    numeros = {art["numero"] for art in articles}
    assert 1 not in numeros, "Art. 1 es del Libro I y no debe estar en el output"
    assert 27 not in numeros, "Art. 27 (Tentativa) es del Libro I y no debe estar en el output"
    assert {101, 103, 239}.issubset(numeros), f"Faltan artículos del Libro II: {numeros}"


def test_articles_have_libro_segundo(articles):
    for art in articles:
        assert "LIBRO SEGUNDO" in art["libro"].upper(), (
            f"cp_art_{art['numero']}: libro no es Libro Segundo: '{art['libro']}'"
        )


# ---------------------------------------------------------------------------
# Nombre del delito (título en <em> tras el número de artículo)
# ---------------------------------------------------------------------------


def test_article_nombre_matches_delito():
    articles_by_id = {a["id"]: a for a in parse_articles(SAMPLE_HTML, SOURCE_URL)}
    assert articles_by_id["cp_art_101"]["nombre"] == "Genocidio"
    assert articles_by_id["cp_art_103"]["nombre"] == "Homicidio"
    assert articles_by_id["cp_art_239"]["nombre"] == "Hurto"


# ---------------------------------------------------------------------------
# Texto vigente vs. "Norma Anterior" (versiones derogadas)
# ---------------------------------------------------------------------------


def test_derogated_norma_anterior_text_excluded(articles):
    """El Art. 101 del fixture tiene una versión derogada marcada 'Norma Anterior' /
    'Texto Anterior' con el centinela DEROGADO_SENTINELA. No debe filtrarse al output."""
    art101 = next(a for a in articles if a["numero"] == 101)
    assert "DEROGADO_SENTINELA" not in art101["texto"]
    assert "Norma Anterior" not in art101["texto"]
    assert "Texto Anterior" not in art101["texto"]


def test_article_with_multiple_paragraphs_joins_text(articles):
    """El Art. 101 tiene dos párrafos vigentes; el texto debe incluir ambos."""
    art101 = next(a for a in articles if a["numero"] == 101)
    assert "destruir total o parcialmente" in art101["texto"]
    assert "ciento sesenta (160)" in art101["texto"]


def test_exequibilidad_notes_excluded_from_texto(articles):
    """Las notas 'Nota: ... declarado EXEQUIBLE/INEXEQUIBLE ...' son anotaciones
    editoriales, no texto de la norma."""
    art101 = next(a for a in articles if a["numero"] == 101)
    assert "declarado EXEQUIBLE" not in art101["texto"]
    assert "Nota:" not in art101["texto"]


# ---------------------------------------------------------------------------
# Artículos con sufijo de letra (ej. 103A, 104A) — descubierto contra HTML real:
# la Ley 599/2000 numera muchas adiciones posteriores como "103A", "104A", "68B",
# etc. Sin manejo explícito, el regex original truncaba "103A" a numero=103,
# colisionando id y contenido con el Art. 103 real.
# ---------------------------------------------------------------------------


def test_lettered_sub_article_gets_distinct_id(articles):
    ids = {a["id"] for a in articles}
    assert "cp_art_103" in ids
    assert "cp_art_103_a" in ids, "Art. 103A debe generar un id propio, no colisionar con 103"
    assert "cp_art_104_a" in ids


def test_lettered_sub_article_has_own_numero_and_texto(articles):
    art103 = next(a for a in articles if a["id"] == "cp_art_103")
    art103a = next(a for a in articles if a["id"] == "cp_art_103_a")

    assert art103["numero"] == 103
    assert art103a["numero"] == 103, "numero base se mantiene, la letra vive en 'id'/'sufijo'"

    assert "El que matare a otro" in art103["texto"]
    assert "niño, niña o adolescente" in art103a["texto"]
    # No deben mezclarse los cuerpos de los dos artículos
    assert "El que matare a otro" not in art103a["texto"]
    assert "niño, niña o adolescente" not in art103["texto"]


def test_lettered_sub_article_derogated_text_excluded(articles):
    for art in articles:
        assert "DEROGADO_SENTINELA_103A" not in art["texto"]


def test_lettered_sub_article_nombre_from_em_tag(articles):
    """104A: el nombre del delito vive en <em>Feminicidio.</em>, el <strong> solo trae el número."""
    art104a = next(a for a in articles if a["id"] == "cp_art_104_a")
    assert "Feminicidio" in art104a["nombre"]


def test_lettered_sub_article_nombre_fallback_from_strong(articles):
    """103A: no hay <em>; el nombre del delito va dentro del propio <strong>."""
    art103a = next(a for a in articles if a["id"] == "cp_art_103_a")
    assert "Agravaci" in art103a["nombre"]


def test_article_with_period_outside_strong_is_recognized(articles):
    """Art. 116: el <strong> cierra justo tras el número; el punto y el nombre
    quedan fuera (texto plano + <em>). Descubierto contra HTML real: un lookahead
    de punto demasiado estricto lo hacía desaparecer silenciosamente."""
    ids = {a["id"] for a in articles}
    assert "cp_art_116" in ids
    art116 = next(a for a in articles if a["id"] == "cp_art_116")
    assert art116["numero"] == 116
    assert art116["sufijo"] is None
    assert "organo o miembro" in art116["nombre"].lower()
    assert "pérdida de la función" in art116["texto"]


def test_lowercase_word_after_article_not_treated_as_suffix(articles):
    """Art. 123: más adelante en el mismo párrafo hay un <strong><u>o en mujer
    menor de catorce años</u></strong> (énfasis judicial). _strong_text concatena
    TODOS los <strong> del párrafo, así que el bold_text queda 'ARTÍCULO 123 o en
    mujer...'. Descubierto contra HTML real: con IGNORECASE, la 'o' minúscula de
    la palabra 'o' se leía como sufijo 'O', generando un cp_art_123o inexistente
    y perdiendo esa cláusula del cuerpo del Art. 123 real."""
    ids = {a["id"] for a in articles}
    assert "cp_art_123" in ids
    assert not any(i.startswith("cp_art_123") and i != "cp_art_123" for i in ids), (
        f"No debe existir un artículo '123<letra>' espurio: {ids}"
    )
    art123 = next(a for a in articles if a["id"] == "cp_art_123")
    assert art123["sufijo"] is None
    assert "o en mujer menor de catorce años" in art123["texto"]


def test_spaced_letter_suffix_recognized(articles):
    """Art. 134 A (con espacio, a diferencia de '103A' pegado) debe reconocerse
    como sufijo de letra, no fusionarse con el Art. 134 base ni perderse."""
    ids = {a["id"] for a in articles}
    assert "cp_art_134_a" in ids
    art134a = next(a for a in articles if a["id"] == "cp_art_134_a")
    assert art134a["numero"] == 134
    assert art134a["sufijo"] == "A"
    assert "DISCRIMINACIÓN" in art134a["nombre"].upper()


def test_hyphenated_letter_suffix_recognized(articles):
    """Art. 243-A: sufijo separado por guion (a diferencia de '103A' pegado y
    '134 A' con espacio). Descubierto contra HTML real: sin soportar '-' como
    separador, '243-A' truncaba a numero=243, colisionando con el Art. 243 base."""
    ids = {a["id"] for a in articles}
    assert "cp_art_243" in ids
    assert "cp_art_243_a" in ids
    art243 = next(a for a in articles if a["id"] == "cp_art_243")
    art243a = next(a for a in articles if a["id"] == "cp_art_243_a")
    assert art243["numero"] == 243 and art243a["numero"] == 243
    assert "Abigeato" in art243["texto"]
    assert art243a["sufijo"] == "A"
    assert "agravación" in art243a["texto"].lower()
    assert "agravación" not in art243["texto"].lower()


def test_hyphenated_numeric_suffix_recognized(articles):
    """Art. 269-1: el sufijo tras el guion es un NÚMERO, no una letra (a
    diferencia de '243-A'). El id usa '_' como separador precisamente para no
    generar 'cp_art_2691', ambiguo con un hipotético artículo 2691."""
    ids = {a["id"] for a in articles}
    assert "cp_art_269" in ids
    assert "cp_art_269_1" in ids
    art269 = next(a for a in articles if a["id"] == "cp_art_269")
    art269_1 = next(a for a in articles if a["id"] == "cp_art_269_1")
    assert art269["numero"] == 269 and art269_1["numero"] == 269
    assert art269_1["sufijo"] == "1"
    assert "patrimonio cultural sumergido" in art269_1["nombre"].lower()
    assert "Reparacion" in art269["nombre"]


# ---------------------------------------------------------------------------
# titulo / capitulo tracking
# ---------------------------------------------------------------------------


def test_titulo_tracked_across_articles(articles):
    art239 = next(a for a in articles if a["numero"] == 239)
    assert "PATRIMONIO ECON" in art239["titulo"].upper()


def test_capitulo_tracked_for_articles(articles):
    art103 = next(a for a in articles if a["numero"] == 103)
    assert art103["capitulo"] is not None
    assert "HOMICIDIO" in art103["capitulo"].upper()


# ---------------------------------------------------------------------------
# build_metadata
# ---------------------------------------------------------------------------


def test_article_count_matches_metadata(articles):
    meta = build_metadata(articles, SOURCE_URL)
    assert meta["total_articles"] == len(articles)


def test_metadata_has_required_fields(articles):
    meta = build_metadata(articles, SOURCE_URL)
    required = {"title", "source_url", "scraped_at", "total_articles"}
    missing = required - meta.keys()
    assert not missing, f"metadata le faltan campos: {missing}"


def test_metadata_source_url_matches(articles):
    meta = build_metadata(articles, SOURCE_URL)
    assert meta["source_url"] == SOURCE_URL


def test_metadata_scraped_at_is_iso_timestamp(articles):
    meta = build_metadata(articles, SOURCE_URL)
    datetime.fromisoformat(meta["scraped_at"])  # no debe lanzar


# ---------------------------------------------------------------------------
# fetch_page
# ---------------------------------------------------------------------------


def test_fetch_page_saves_raw_html(tmp_path, httpx_mock):
    html_content = "<html><body>test</body></html>"
    httpx_mock.add_response(text=html_content, status_code=200)

    raw_path = tmp_path / "raw.html"
    result = fetch_page(SOURCE_URL, raw_path)

    assert result == html_content
    assert raw_path.exists(), "El archivo HTML no fue guardado en disco"
    assert raw_path.read_text(encoding="utf-8") == html_content


def test_fetch_page_raises_on_http_error(httpx_mock):
    httpx_mock.add_response(status_code=500)

    with pytest.raises(Exception, match="500"):
        fetch_page(SOURCE_URL, Path("/tmp/ignored.html"))
