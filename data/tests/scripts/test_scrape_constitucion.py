import json
import re
from pathlib import Path

from data.scripts.scrape_constitucion import parse_articles
from data.scripts.scrape_constitucion import build_metadata

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_HTML = (FIXTURES_DIR / "constitucion_sample.html").read_text(encoding="utf-8")
SOURCE_URL = "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4125"



def _parse_articles(html, url):
    return parse_articles(html, url)


def _build_metadata(articles, url):
    return build_metadata(articles, url)


def test_parse_articles_returns_list():
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)

    assert isinstance(articles, list)
    assert len(articles) > 0


def test_article_has_required_fields():
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)

    required = {"id", "numero", "titulo", "texto", "url_original"}

    for art in articles:
        missing = required - art.keys()
        assert not missing, f"Artículo {art.get('id')} le faltan campos: {missing}"
        assert "capitulo" in art


def test_article_id_format():
    """El id sigue el patrón 'art_<numero>' (ej: 'art_1', 'art_42')."""
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    pattern = re.compile(r"^art_\d+$")
    for art in articles:
        assert pattern.match(art["id"]), (
            f"id inválido: '{art['id']}' — debe seguir el patrón art_<número>"
        )


def test_article_numero_is_positive_int():
    """numero es un entero positivo."""
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    for art in articles:
        assert isinstance(art["numero"], int), f"numero debe ser int, got {type(art['numero'])}"
        assert art["numero"] > 0, f"numero debe ser positivo, got {art['numero']}"


def test_article_texto_no_html_tags():
    """texto no contiene '<' ni '>' — sin artefactos HTML."""
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    for art in articles:
        assert "<" not in art["texto"], (
            f"art_{art['numero']}: texto contiene '<': {art['texto'][:80]}"
        )
        assert ">" not in art["texto"], (
            f"art_{art['numero']}: texto contiene '>': {art['texto'][:80]}"
        )


def test_article_texto_is_nonempty():
    """texto no está vacío."""
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    for art in articles:
        assert art["texto"].strip(), f"art_{art['numero']}: texto está vacío"


def test_article_titulo_is_nonempty_string():
    """titulo es un string con contenido."""
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    for art in articles:
        assert isinstance(art["titulo"], str), f"titulo debe ser str"
        assert art["titulo"].strip(), f"art_{art['numero']}: titulo está vacío"


def test_article_url_original_contains_source():
    """url_original contiene la URL base y una referencia al artículo."""
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    base = "funcionpublica.gov.co"
    for art in articles:
        assert base in art["url_original"], (
            f"art_{art['numero']}: url_original no contiene el dominio: {art['url_original']}"
        )


def test_no_transitorios_in_output():
    """Ningún artículo transitorio aparece en el output."""
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    for art in articles:
        assert "transitorio" not in art["id"].lower(), (
            f"Artículo transitorio en output: {art['id']}"
        )
        assert "transitorio" not in art["titulo"].lower(), (
            f"Título transitorio en output: {art['titulo']}"
        )


def test_sample_contains_expected_articles():
    """El fixture tiene artículos 1, 2, 3, 11, 12, 42 — todos deben aparecer."""
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    numeros = {art["numero"] for art in articles}
    expected = {1, 2, 3, 11, 12, 42}
    assert expected.issubset(numeros), (
        f"Faltan artículos en el output. Esperados: {expected}, encontrados: {numeros}"
    )


def test_article_with_multiple_paragraphs_joins_text():
    """
    Artículo 2 tiene dos párrafos en el fixture; su texto debe incluir ambos.
    """
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    art2 = next((a for a in articles if a["numero"] == 2), None)
    assert art2 is not None, "Artículo 2 no encontrado"
    assert "fines esenciales" in art2["texto"], "Falta el primer párrafo del Art. 2"
    assert "autoridades de la República" in art2["texto"], (
        "Falta el segundo párrafo del Art. 2"
    )


def test_titulo_tracked_across_articles():
    """
    Los artículos bajo TITULO II tienen 'TITULO II' en su campo titulo.
    """
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    titulo2_arts = [a for a in articles if a["numero"] in {11, 12, 42}]
    assert titulo2_arts, "No se encontraron artículos del Título II"
    for art in titulo2_arts:
        assert "TITULO II" in art["titulo"], (
            f"Art. {art['numero']}: titulo no refleja el Título II: '{art['titulo']}'"
        )


def test_capitulo_tracked_for_articles():
    """
    Artículo 42 pertenece al Capítulo 2; su campo capitulo no debe ser None.
    """
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    art42 = next((a for a in articles if a["numero"] == 42), None)
    assert art42 is not None, "Artículo 42 no encontrado"
    assert art42["capitulo"] is not None, (
        "Art. 42 debería tener capitulo asignado, encontrado None"
    )


# ---------------------------------------------------------------------------
# build_metadata
# ---------------------------------------------------------------------------

def test_article_count_matches_metadata():
    """len(articles) == metadata['total_articles']."""
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    meta = _build_metadata(articles, SOURCE_URL)
    assert meta["total_articles"] == len(articles), (
        f"metadata.total_articles={meta['total_articles']} != len(articles)={len(articles)}"
    )


def test_metadata_has_required_fields():
    """metadata tiene title, source_url, scraped_at, total_articles."""
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    meta = _build_metadata(articles, SOURCE_URL)
    required = {"title", "source_url", "scraped_at", "total_articles"}
    missing = required - meta.keys()
    assert not missing, f"metadata le faltan campos: {missing}"


def test_metadata_source_url_matches():
    """metadata.source_url es la URL que se le pasó."""
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    meta = _build_metadata(articles, SOURCE_URL)
    assert meta["source_url"] == SOURCE_URL


def test_metadata_scraped_at_is_iso_timestamp():
    """metadata.scraped_at es un timestamp ISO 8601 válido."""
    from datetime import datetime
    articles = _parse_articles(SAMPLE_HTML, SOURCE_URL)
    meta = _build_metadata(articles, SOURCE_URL)
    # Should not raise
    datetime.fromisoformat(meta["scraped_at"])


# ---------------------------------------------------------------------------
# fetch_page
# ---------------------------------------------------------------------------

def test_fetch_page_saves_raw_html(tmp_path, httpx_mock):
    """fetch_page guarda el HTML en disco y lo retorna."""
    from data.scripts.scrape_constitucion import fetch_page

    html_content = "<html><body>test</body></html>"
    httpx_mock.add_response(text=html_content, status_code=200)

    raw_path = tmp_path / "raw.html"
    result = fetch_page(SOURCE_URL, raw_path)

    assert result == html_content
    assert raw_path.exists(), "El archivo HTML no fue guardado en disco"
    assert raw_path.read_text(encoding="utf-8") == html_content


def test_fetch_page_raises_on_http_error(httpx_mock):
    """fetch_page lanza una excepción clara cuando el servidor responde 500."""
    from data.scripts.scrape_constitucion import fetch_page
    import httpx

    httpx_mock.add_response(status_code=500)

    with pytest.raises(Exception, match="500"):
        fetch_page(SOURCE_URL, Path("/tmp/ignored.html"))
