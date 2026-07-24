import re
from datetime import datetime
from pathlib import Path

import pytest

from data.scripts.scrape_codigo_sustantivo_trabajo import (
    build_metadata,
    fetch_page,
    parse_articles,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_HTML = (FIXTURES_DIR / "codigo_sustantivo_trabajo_sample.html").read_text(encoding="utf-8")
SOURCE_URL = "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=199983"


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
    required = {"id", "numero", "nombre", "parte", "titulo", "capitulo", "texto", "url_original"}
    for art in articles:
        missing = required - art.keys()
        assert not missing, f"Artículo {art.get('id')} le faltan campos: {missing}"


def test_article_id_format(articles):
    """El id sigue el patrón 'cst_art_<numero>[_sufijo]' (ej: 'cst_art_97',
    'cst_art_97_a', 'cst_art_391_1'). El sufijo puede ser letra o número."""
    pattern = re.compile(r"^cst_art_\d+(_[a-z0-9]+)?$")
    for art in articles:
        assert pattern.match(art["id"]), (
            f"id inválido: '{art['id']}' — debe seguir el patrón cst_art_<número>[_sufijo]"
        )


def test_article_numero_is_positive_int(articles):
    for art in articles:
        assert isinstance(art["numero"], int), f"numero debe ser int, got {type(art['numero'])}"
        assert art["numero"] > 0


def test_article_texto_no_html_tags(articles):
    for art in articles:
        assert "<" not in art["texto"], f"cst_art_{art['numero']}: texto contiene '<'"
        assert ">" not in art["texto"], f"cst_art_{art['numero']}: texto contiene '>'"


def test_article_texto_is_nonempty(articles):
    for art in articles:
        assert art["texto"].strip(), f"cst_art_{art['numero']}: texto está vacío"


def test_article_url_original_contains_source(articles):
    base = "funcionpublica.gov.co"
    for art in articles:
        assert base in art["url_original"], (
            f"cst_art_{art['numero']}: url_original no contiene el dominio"
        )


# ---------------------------------------------------------------------------
# Alcance: CST completo (decidido con el usuario, 2026-07-23) — a diferencia de
# Código Penal, aquí no se descarta ninguna parte del documento.
# ---------------------------------------------------------------------------


def test_articles_from_all_three_partes_are_included(articles):
    numeros = {art["numero"] for art in articles}
    assert {1, 61, 391}.issubset(numeros), (
        "Deben incluirse artículos de la Primera y Segunda Parte"
    )
    assert 485 in numeros, "Debe incluirse un artículo de la Tercera Parte"


# ---------------------------------------------------------------------------
# Jerarquía: parte / titulo / capitulo
# ---------------------------------------------------------------------------


def test_first_parte_defaults_when_unlabeled():
    """La Primera Parte no tiene rótulo propio en la fuente (arranca directo en
    'TITULO PRELIMINAR'). Se le asigna un valor por defecto."""
    art1 = next(a for a in parse_articles(SAMPLE_HTML, SOURCE_URL) if a["numero"] == 1)
    assert "PRIMERA PARTE" in art1["parte"].upper()


def test_parte_tracked_after_explicit_heading(articles):
    art391 = next(a for a in articles if a["numero"] == 391)
    assert "SEGUNDA PARTE" in art391["parte"].upper()
    assert "DERECHO COLECTIVO" in art391["parte"].upper()

    art485 = next(a for a in articles if a["numero"] == 485)
    assert "TERCERA PARTE" in art485["parte"].upper()


def test_titulo_resets_across_partes(articles):
    """El número de TITULO se reinicia en cada PARTE — el TITULO I de la Segunda
    Parte (Sindicatos) es distinto del TITULO I de la Tercera Parte (Vigilancia)."""
    art391 = next(a for a in articles if a["numero"] == 391)
    art485 = next(a for a in articles if a["numero"] == 485)
    assert "SINDICATOS" in art391["titulo"].upper()
    assert "VIGILANCIA" in art485["titulo"].upper()


def test_capitulo_tracked_for_articles(articles):
    art61 = next(a for a in articles if a["numero"] == 61)
    assert art61["capitulo"] is not None
    assert "JUSTAS CAUSAS" in art61["capitulo"].upper()


# ---------------------------------------------------------------------------
# Artículo con lista de literales en párrafos separados, intercalada con
# anotaciones — descubierto contra HTML real (Art. 61: cada causal es un <p>
# aparte, con notas de exequibilidad de por medio).
# ---------------------------------------------------------------------------


def test_article_joins_list_items_across_paragraphs(articles):
    art61 = next(a for a in articles if a["numero"] == 61)
    assert "Por muerte del trabajador" in art61["texto"]
    assert "Por mutuo consentimiento" in art61["texto"]
    assert "Por expiración del plazo fijo pactado" in art61["texto"]
    assert "Por terminación de la obra o labor contratada" in art61["texto"]


# ---------------------------------------------------------------------------
# Anotaciones de historia/jurisprudencia: párrafo COMPLETO entre paréntesis —
# a diferencia de Código Penal (prefijo "Nota:"), aquí es "(Modificado por...)",
# "(Subrogado por...)", "(Literal c) declarado EXEQUIBLE...)", etc.
# ---------------------------------------------------------------------------


def test_parenthetical_annotations_excluded_from_texto(articles):
    art61 = next(a for a in articles if a["numero"] == 61)
    assert "declarado EXEQUIBLE" not in art61["texto"]
    assert "Subrogado por" not in art61["texto"]

    art64 = next(a for a in articles if a["numero"] == 64)
    assert "Modificado por" not in art64["texto"]


# ---------------------------------------------------------------------------
# "Norma Anterior" / "Texto Anterior" — mismo patrón que Código Penal.
# ---------------------------------------------------------------------------


def test_derogated_norma_anterior_text_excluded(articles):
    art238 = next(a for a in articles if a["numero"] == 238)
    assert "DEROGADO_SENTINELA_238" not in art238["texto"]
    assert "Norma Anterior" not in art238["texto"]
    assert "Texto Anterior" not in art238["texto"]


# ---------------------------------------------------------------------------
# Placeholder sin resolver: "{empleador}" → limpiar llaves, dejar la palabra.
# ---------------------------------------------------------------------------


def test_placeholder_braces_are_stripped(articles):
    art62 = next(a for a in articles if a["numero"] == 62)
    assert "{empleador}" not in art62["texto"]
    assert "empleador" in art62["texto"]


# ---------------------------------------------------------------------------
# Artículos con sufijo (letra o guion-número) — mismo patrón que Código Penal.
# ---------------------------------------------------------------------------


def test_lettered_sub_article_gets_distinct_id(articles):
    ids = {a["id"] for a in articles}
    assert "cst_art_97" in ids
    assert "cst_art_97_a" in ids, "Art. 97A debe generar un id propio, no colisionar con 97"


def test_lettered_sub_article_has_own_texto(articles):
    art97 = next(a for a in articles if a["id"] == "cst_art_97")
    art97a = next(a for a in articles if a["id"] == "cst_art_97_a")
    assert "agentes independientes" in art97["texto"].lower()
    assert "colocadores de apuestas" in art97a["texto"].lower()
    assert "colocadores de apuestas" not in art97["texto"].lower()


def test_hyphenated_suffix_recognized(articles):
    ids = {a["id"] for a in articles}
    assert "cst_art_391" in ids
    assert "cst_art_391_1" in ids
    art391_1 = next(a for a in articles if a["id"] == "cst_art_391_1")
    assert art391_1["sufijo"] == "1"
    assert "subdirectivas seccionales" in art391_1["texto"].lower()


def test_inline_em_emphasis_not_mistaken_for_nombre(articles):
    """Descubierto contra HTML real (Art. 391-1): a diferencia de Código Penal
    (donde <em> siempre marca el nombre del delito), aquí <em> a veces se usa
    para énfasis DENTRO del cuerpo del artículo — el nombre real vive completo
    en el <strong> de encabezado ('ARTICULO 391-1. DIRECTIVAS SECCIONALES.').
    Sin este resguardo, el nombre terminaba siendo el fragmento en <em>
    ('en aquellos municipios...') en vez del título real."""
    art391_1 = next(a for a in articles if a["id"] == "cst_art_391_1")
    assert art391_1["nombre"] == "DIRECTIVAS SECCIONALES"
    assert "municipios" not in art391_1["nombre"].lower()


# ---------------------------------------------------------------------------
# Artículo sin número (heading roto en dos <strong> consecutivos: "AR" +
# "TÍCULO. PROHIBICIÓN") — descubierto contra HTML real (Segunda Parte, Pactos
# Colectivos, adicionado por el Art. 70 de la Ley 50/1990 sin número formal en
# esta fuente). Decisión: se descarta, hueco consciente — no debe colarse en el
# artículo anterior ni generar un artículo espurio.
# ---------------------------------------------------------------------------


def test_unnumbered_article_is_skipped_entirely(articles):
    for art in articles:
        assert "DEROGADO_SENTINELA_SINNUMERO" not in art["texto"], (
            f"cst_art_{art['numero']}: el artículo sin número no debe fusionarse en otro"
        )


def test_unnumbered_article_does_not_corrupt_previous_article(articles):
    art481 = next(a for a in articles if a["numero"] == 481)
    assert "sindicalizados se rigen" in art481["texto"].lower()
    assert "prohibición" not in art481["texto"].lower()


# ---------------------------------------------------------------------------
# <button>Jurisprudencia Vigencia</button> — filtrado, mismo patrón que Código Penal.
# ---------------------------------------------------------------------------


def test_button_text_not_included_in_texto(articles):
    art66 = next(a for a in articles if a["numero"] == 66)
    assert "Jurisprudencia Vigencia" not in art66["texto"]


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
