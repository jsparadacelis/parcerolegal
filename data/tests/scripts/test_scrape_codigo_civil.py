import re
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from data.scripts.scrape_codigo_civil import (
    build_metadata,
    fetch_pages,
    parse_articles,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SOURCE_URL = "http://www.secretariasenado.gov.co/senado/basedoc/codigo_civil.html"
SECOND_PAGE_URL = "http://www.secretariasenado.gov.co/senado/basedoc/codigo_civil_pr001.html"


@pytest.fixture
def sample_pages():
    return [
        (SOURCE_URL, (FIXTURES_DIR / "codigo_civil_sample.html").read_text(encoding="utf-8")),
        (SECOND_PAGE_URL, (FIXTURES_DIR / "codigo_civil_sample_pr001.html").read_text(encoding="utf-8")),
    ]


@pytest.fixture
def articles(sample_pages):
    return parse_articles(sample_pages)


@pytest.fixture
def articles_by_id(articles):
    return {art["id"]: art for art in articles}


@pytest.fixture
def first_page_html():
    return (
        '<html><body><p style="text-align:center;">'
        '<a class=antsig href="codigo_civil_pr001.html">Siguiente</a></p>'
        "<p>Art&iacute;culo uno</p></body></html>"
    )


@pytest.fixture
def last_page_html():
    return (
        '<html><body><p style="text-align:center;">'
        '<a class=antsig href="codigo_civil.html">Anterior</a></p>'
        "<p>Fin</p></body></html>"
    )


# ---------------------------------------------------------------------------
# parse_articles — forma general
# ---------------------------------------------------------------------------


def test_parse_articles_returns_every_numbered_article_in_order(articles):
    assert [art["id"] for art in articles] == [
        "cc_art_1",
        "cc_art_2",
        "cc_art_18",
        "cc_art_33",
        "cc_art_34",
        "cc_art_35",
        "cc_art_143",
        "cc_art_156",
        "cc_art_269",
        "cc_art_410",
        "cc_art_1781",
        "cc_art_1781_a",
        "cc_art_1782",
        "cc_art_2349",
        "cc_art_2378",
        "cc_art_2379",
    ]


def test_article_has_required_fields(articles):
    required = {
        "id", "numero", "sufijo", "nombre", "libro", "titulo", "capitulo", "texto", "url_original",
    }
    for art in articles:
        missing = required - art.keys()
        assert not missing, f"{art.get('id')} le faltan campos: {missing}"


def test_article_ids_are_unique(articles):
    ids = [art["id"] for art in articles]
    assert len(ids) == len(set(ids))


def test_article_texto_has_no_editorial_markers_or_html(articles):
    for art in articles:
        assert "<" not in art["texto"], f"{art['id']}: texto contiene '<'"
        assert ">" not in art["texto"], f"{art['id']}: texto contiene '>'"


# ---------------------------------------------------------------------------
# Numeración: ordinales, sufijos, encabezados partidos por el anchor
# ---------------------------------------------------------------------------


def test_ordinal_suffix_is_not_mistaken_for_article_suffix(articles_by_id):
    """'ARTÍCULO 1o.' es la forma ordinal del Art. 1, no un Art. '1 O'."""
    art1 = articles_by_id["cc_art_1"]
    assert art1["numero"] == 1
    assert art1["sufijo"] is None


def test_lettered_article_gets_distinct_id_and_sufijo(articles_by_id):
    art = articles_by_id["cc_art_1781_a"]
    assert art["numero"] == 1781
    assert art["sufijo"] == "A"
    assert art["texto"].startswith("No forman parte del haber social")


def test_lettered_article_does_not_swallow_base_article(articles_by_id):
    assert "No forman parte" not in articles_by_id["cc_art_1781"]["texto"]


def test_heading_split_by_anchor_tag_is_detected(articles_by_id):
    """En la fuente real el anchor corta el encabezado: '<a>ARTÍCULO</a> 143.' y
    '<a>A</a>RTÍCULO 410.'. Sin tolerarlo, ambos artículos se fusionarían en el
    anterior."""
    assert articles_by_id["cc_art_143"]["nombre"] == "NULIDAD POR MATRIMONIO DE IMPÚBER"
    assert articles_by_id["cc_art_410"]["nombre"] == "REGISTRO DEL ESTADO CIVIL"
    assert "nulidad" not in articles_by_id["cc_art_35"]["texto"].lower()


def test_url_original_points_to_real_anchor_in_its_page(articles_by_id):
    assert articles_by_id["cc_art_1"]["url_original"] == f"{SOURCE_URL}#1"
    assert articles_by_id["cc_art_1781"]["url_original"] == f"{SECOND_PAGE_URL}#1781"
    assert articles_by_id["cc_art_1781_a"]["url_original"] == f"{SECOND_PAGE_URL}#1781A"


# ---------------------------------------------------------------------------
# Nombre del artículo: dos formas en la fuente
# ---------------------------------------------------------------------------


def test_nombre_from_editor_angle_brackets(articles_by_id):
    assert articles_by_id["cc_art_1781"]["nombre"] == "COMPOSICIÓN DE HABER DE LA SOCIEDAD CONYUGAL"


def test_nombre_from_legal_uppercase_heading(articles_by_id):
    """Artículos reformados recientemente traen el nombre oficial sin '<>'."""
    art = articles_by_id["cc_art_156"]
    assert art["nombre"] == "LEGITIMACIÓN Y OPORTUNIDAD PARA PRESENTAR LA DEMANDA"
    assert art["texto"] == "El divorcio solo podrá ser demandado por los cónyuges."


def test_derogation_note_is_not_taken_as_nombre(articles_by_id):
    assert articles_by_id["cc_art_269"]["nombre"] == ""


def test_nombre_with_nested_editor_substitution(articles_by_id):
    """'<DAÑOS CAUSADOS POR LOS <TRABAJADORES>.': el editor anidó un reemplazo
    dentro del nombre."""
    assert articles_by_id["cc_art_2349"]["nombre"] == "DAÑOS CAUSADOS POR LOS TRABAJADORES"


def test_note_opened_inside_heading_anchor_is_still_removed(articles_by_id):
    """'<a>ARTÍCULO 18. <OBLIGATORIEDAD DE LA LEY>.<</a>Ver Notas del Editor>': el
    '<' de la nota quedó dentro del anchor del encabezado."""
    art = articles_by_id["cc_art_18"]
    assert art["nombre"] == "OBLIGATORIEDAD DE LA LEY"
    assert art["texto"].startswith("La ley es obligatoria")


def test_nombre_with_unclosed_angle_bracket(articles_by_id):
    """'<TRANSMISIBILIDAD DE LA FIANZA' sin '>' en la fuente: el nombre termina
    donde termina el anchor del encabezado."""
    art = articles_by_id["cc_art_2378"]
    assert art["nombre"] == "TRANSMISIBILIDAD DE LA FIANZA"
    assert art["texto"] == "Los derechos y obligaciones de los fiadores son transmisibles a sus herederos."


# ---------------------------------------------------------------------------
# Texto del artículo
# ---------------------------------------------------------------------------


def test_editor_substitutions_keep_the_replacement_word(articles_by_id):
    """'Los <empleadores> [tachado: amos]': el editor reemplaza el término
    derogado por el vigente entre <>, en minúscula. Esa palabra SÍ es norma."""
    texto = articles_by_id["cc_art_2349"]["texto"]
    assert texto.startswith("Los empleadores responderán del daño causado por sus trabajadores, con")


def test_sic_marker_is_dropped(articles_by_id):
    assert "sic" not in articles_by_id["cc_art_2349"]["texto"]
    assert "por éstos a aquéllos." in articles_by_id["cc_art_2349"]["texto"]


def test_unclosed_editor_note_paragraph_is_dropped(articles_by_id):
    assert articles_by_id["cc_art_2379"]["texto"] == "El fiador reconvenido goza del beneficio de excusión."


def test_texto_excludes_heading(articles_by_id):
    assert articles_by_id["cc_art_1"]["texto"].startswith("El Código Civil comprende")


def test_editor_notes_are_stripped_from_texto(articles_by_id):
    art143 = articles_by_id["cc_art_143"]["texto"]
    assert art143 == "La nulidad a que se contrae el numeral 2 podrá ser alegada por los padres."


def test_struck_inexequible_text_is_excluded(articles_by_id):
    """<S> marca apartes tachados (declarados INEXEQUIBLES): no son norma vigente."""
    texto = articles_by_id["cc_art_33"]["texto"]
    assert texto.startswith("La palabra persona, en su sentido general")
    assert "hombre" not in texto


def test_editor_footnote_asterisks_are_stripped(articles_by_id):
    assert "*" not in articles_by_id["cc_art_34"]["texto"]
    assert "veintiún años" in articles_by_id["cc_art_34"]["texto"]


def test_article_joins_paragraphs(articles_by_id):
    texto = articles_by_id["cc_art_34"]["texto"]
    assert "Llámase infante" in texto
    assert "habilitación de edad" in texto


def test_article_joins_numbered_items(articles_by_id):
    texto = articles_by_id["cc_art_1781"]["texto"]
    assert "1.) De los salarios" in texto
    assert "2.) De todos los frutos" in texto


def test_fully_derogated_article_has_empty_texto(articles_by_id):
    """Se conserva el artículo (numeración completa) pero sin texto: su único
    contenido en la fuente es la nota de derogatoria del editor."""
    assert articles_by_id["cc_art_269"]["texto"] == ""
    assert articles_by_id["cc_art_410"]["texto"] == ""


def test_preamble_before_first_article_is_ignored(articles_by_id):
    assert "Ley 57 de 1887" not in articles_by_id["cc_art_1"]["texto"]


def test_page_footer_copyright_is_not_appended(articles_by_id):
    assert "derecho de autor" not in articles_by_id["cc_art_2"]["texto"]


def test_unlabeled_centered_subheading_closes_article(articles_by_id):
    assert "CAUSA LICITA" not in articles_by_id["cc_art_1781_a"]["texto"]


def test_closing_signatures_are_not_appended_to_last_article(articles_by_id):
    texto = articles_by_id["cc_art_2379"]["texto"]
    assert "MURILLO" not in texto
    assert "FIN DEL CÓDIGO" not in texto


# ---------------------------------------------------------------------------
# Jerarquía: LIBRO → TÍTULO → CAPÍTULO
# ---------------------------------------------------------------------------


def test_titulo_preliminar_has_no_libro(articles_by_id):
    art1 = articles_by_id["cc_art_1"]
    assert art1["libro"] is None
    assert art1["titulo"] == "TÍTULO PRELIMINAR"
    assert art1["capitulo"] == "CAPÍTULO I. OBJETO Y FUERZA DE ESTE CÓDIGO"


def test_libro_titulo_and_capitulo_are_tracked(articles_by_id):
    art = articles_by_id["cc_art_1781"]
    assert art["libro"] == "LIBRO CUARTO. DE LAS OBLIGACIONES EN GENERAL Y DE LOS CONTRATOS"
    assert art["titulo"] == "TÍTULO XXII. DE LAS CAPITULACIONES MATRIMONIALES Y DE LA SOCIEDAD CONYUGAL"
    assert art["capitulo"] == "CAPÍTULO I. REGLAS GENERALES"


def test_libro_heading_carries_across_pages(articles_by_id):
    assert articles_by_id["cc_art_33"]["libro"] == "LIBRO PRIMERO. DE LAS PERSONAS"


def test_paragrafo_heading_does_not_leak_into_capitulo(articles_by_id):
    assert articles_by_id["cc_art_156"]["capitulo"] == (
        "CAPÍTULO V. DEFINICIONES DE VARIAS PALABRAS DE USO FRECUENTE EN LAS LEYES"
    )


def test_new_titulo_resets_capitulo(sample_pages):
    html = (
        "<html><body>"
        '<p class="centrado"><a name="Nivel1">CAP&Iacute;TULO I.</a></p>'
        '<p class="centrado">GENERALIDADES</p>'
        '<p class="centrado"><a name="Nivel2">T&Iacute;TULO II.</a></p>'
        '<p class="centrado">DEL MATRIMONIO</p>'
        '<p><a name="113">ART&Iacute;CULO 113. &lt;DEFINICI&Oacute;N&gt;.</a> El matrimonio es un contrato.</p>'
        "</body></html>"
    )
    [art] = parse_articles([(SOURCE_URL, html)])
    assert art["titulo"] == "TÍTULO II. DEL MATRIMONIO"
    assert art["capitulo"] is None


def test_parse_articles_rejects_pages_without_articles():
    with pytest.raises(ValueError, match="artículos"):
        parse_articles([(SOURCE_URL, "<html><body><p>nada</p></body></html>")])


# ---------------------------------------------------------------------------
# build_metadata
# ---------------------------------------------------------------------------


def test_metadata_counts_articles_and_articles_with_texto(articles):
    meta = build_metadata(articles, SOURCE_URL)
    assert meta["total_articles"] == len(articles)
    assert meta["articles_with_texto"] == len(articles) - 2
    assert meta["source_url"] == SOURCE_URL
    assert "Código Civil" in meta["title"]


def test_metadata_scraped_at_is_iso_timestamp(articles):
    meta = build_metadata(articles, SOURCE_URL)
    datetime.fromisoformat(meta["scraped_at"])


# ---------------------------------------------------------------------------
# fetch_pages — la fuente parte el código en ~84 páginas encadenadas
# ---------------------------------------------------------------------------


def test_fetch_pages_follows_siguiente_links_and_caches_raw(
    tmp_path, httpx_mock, first_page_html, last_page_html
):
    httpx_mock.add_response(url=SOURCE_URL, content=first_page_html.encode("latin-1"))
    httpx_mock.add_response(url=SECOND_PAGE_URL, content=last_page_html.encode("latin-1"))

    pages = fetch_pages(SOURCE_URL, tmp_path)

    assert [url for url, _ in pages] == [SOURCE_URL, SECOND_PAGE_URL]
    assert "Art&iacute;culo uno" in pages[0][1]
    assert (tmp_path / "codigo_civil.html").exists()
    assert (tmp_path / "codigo_civil_pr001.html").exists()


def test_fetch_pages_decodes_latin1(tmp_path, httpx_mock):
    httpx_mock.add_response(url=SOURCE_URL, content="<p>Artículo único</p>".encode("latin-1"))

    [(_, html)] = fetch_pages(SOURCE_URL, tmp_path)

    assert "Artículo único" in html


def test_fetch_pages_reuses_cached_raw_without_network(
    tmp_path, httpx_mock, first_page_html, last_page_html
):
    (tmp_path / "codigo_civil.html").write_bytes(first_page_html.encode("latin-1"))
    (tmp_path / "codigo_civil_pr001.html").write_bytes(last_page_html.encode("latin-1"))

    pages = fetch_pages(SOURCE_URL, tmp_path)

    assert len(pages) == 2
    assert httpx_mock.get_requests() == []


def test_fetch_pages_raises_on_http_error(tmp_path, httpx_mock):
    httpx_mock.add_response(url=SOURCE_URL, status_code=500)

    with pytest.raises(httpx.HTTPStatusError, match="500"):
        fetch_pages(SOURCE_URL, tmp_path)


def test_article_id_format(articles):
    pattern = re.compile(r"^cc_art_\d+(_[a-z0-9]+)?$")
    for art in articles:
        assert pattern.match(art["id"]), art["id"]
