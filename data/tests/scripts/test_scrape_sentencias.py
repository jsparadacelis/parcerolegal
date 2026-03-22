import re
from pathlib import Path

import pytest

from data.scripts.scrape_sentencias import (
    SENTENCIAS_LIST,
    clean_text,
    extract_sections,
    parse_metadata,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_HTML = (FIXTURES_DIR / "sentencia_sample.html").read_text(encoding="utf-8")
SOURCE_URL = "https://www.corteconstitucional.gov.co/relatoria/2023/T-999-23.htm"


# ---------------------------------------------------------------------------
# SENTENCIAS_LIST
# ---------------------------------------------------------------------------


def test_sentencias_list_has_required_fields():
    """Cada entrada tiene id, url, tema."""
    required = {"id", "url", "tema"}
    for entry in SENTENCIAS_LIST:
        missing = required - entry.keys()
        assert not missing, f"Entrada {entry.get('id')} le faltan campos: {missing}"


def test_sentencias_list_has_at_least_10():
    assert len(SENTENCIAS_LIST) >= 10


def test_sentencias_list_ids_are_unique():
    ids = [s["id"] for s in SENTENCIAS_LIST]
    assert len(ids) == len(set(ids)), "IDs duplicados en SENTENCIAS_LIST"


# ---------------------------------------------------------------------------
# parse_metadata
# ---------------------------------------------------------------------------


def test_parse_metadata_returns_required_fields():
    meta = parse_metadata(SAMPLE_HTML, "T-999-23", SOURCE_URL)
    required = {
        "sentencia_id",
        "tipo",
        "numero",
        "year",
        "fecha",
        "magistrado_ponente",
        "tema",
        "source_url",
        "scraped_at",
    }
    missing = required - meta.keys()
    assert not missing, f"Metadata le faltan campos: {missing}"


def test_parse_metadata_extracts_magistrado():
    meta = parse_metadata(SAMPLE_HTML, "T-999-23", SOURCE_URL)
    assert "DIANA FAJARDO RIVERA" in meta["magistrado_ponente"].upper()


def test_parse_metadata_extracts_fecha():
    meta = parse_metadata(SAMPLE_HTML, "T-999-23", SOURCE_URL)
    assert "2023" in meta["fecha"]
    assert meta["fecha"].strip()


def test_parse_metadata_extracts_tipo():
    meta = parse_metadata(SAMPLE_HTML, "T-999-23", SOURCE_URL)
    assert meta["tipo"] == "T"


def test_parse_metadata_extracts_numero():
    meta = parse_metadata(SAMPLE_HTML, "T-999-23", SOURCE_URL)
    assert meta["numero"] == "999"


def test_parse_metadata_extracts_year():
    meta = parse_metadata(SAMPLE_HTML, "T-999-23", SOURCE_URL)
    assert meta["year"] == 2023


def test_parse_metadata_source_url():
    meta = parse_metadata(SAMPLE_HTML, "T-999-23", SOURCE_URL)
    assert meta["source_url"] == SOURCE_URL


def test_parse_metadata_scraped_at_is_iso():
    from datetime import datetime

    meta = parse_metadata(SAMPLE_HTML, "T-999-23", SOURCE_URL)
    datetime.fromisoformat(meta["scraped_at"])


# ---------------------------------------------------------------------------
# extract_sections
# ---------------------------------------------------------------------------


def test_extract_sections_returns_dict_with_keys():
    sections = extract_sections(SAMPLE_HTML)
    expected_keys = {"antecedentes", "consideraciones", "resuelve"}
    assert expected_keys == set(sections.keys())


def test_extract_sections_antecedentes_not_empty():
    sections = extract_sections(SAMPLE_HTML)
    assert sections["antecedentes"].strip()


def test_extract_sections_consideraciones_not_empty():
    sections = extract_sections(SAMPLE_HTML)
    assert sections["consideraciones"].strip()


def test_extract_sections_resuelve_not_empty():
    sections = extract_sections(SAMPLE_HTML)
    assert sections["resuelve"].strip()


def test_extract_sections_antecedentes_has_content():
    sections = extract_sections(SAMPLE_HTML)
    assert "tutela" in sections["antecedentes"].lower()


def test_extract_sections_consideraciones_has_content():
    sections = extract_sections(SAMPLE_HTML)
    assert "competencia" in sections["consideraciones"].lower()


def test_extract_sections_resuelve_has_content():
    sections = extract_sections(SAMPLE_HTML)
    assert "CONFIRMAR" in sections["resuelve"]


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------


def test_clean_text_removes_html_tags():
    result = clean_text("<p>Hello <b>world</b></p>")
    assert "<" not in result
    assert ">" not in result
    assert "Hello world" in result


def test_clean_text_removes_mso_artifacts():
    result = clean_text('<p class="MsoNormal">&nbsp;&nbsp; Hello</p>')
    assert "MsoNormal" not in result
    assert "nbsp" not in result


def test_clean_text_normalizes_whitespace():
    result = clean_text("<p>  too   many    spaces  </p>")
    assert "  " not in result
    assert result == "too many spaces"


def test_clean_text_empty_input():
    assert clean_text("") == ""


# ---------------------------------------------------------------------------
# texto_completo
# ---------------------------------------------------------------------------


def test_texto_completo_not_empty():
    """clean_text of the full HTML produces non-empty text."""
    text = clean_text(SAMPLE_HTML)
    assert len(text) > 100


# ---------------------------------------------------------------------------
# fetch_sentencia (mocked)
# ---------------------------------------------------------------------------


def test_fetch_sentencia_saves_html(tmp_path, httpx_mock):
    from data.scripts.scrape_sentencias import fetch_sentencia

    html_content = "<html><body>test sentencia</body></html>"
    httpx_mock.add_response(text=html_content, status_code=200)

    raw_path = tmp_path / "raw" / "sentencia.html"
    result = fetch_sentencia(SOURCE_URL, raw_path)

    assert result == html_content
    assert raw_path.exists()
    assert raw_path.read_text(encoding="utf-8") == html_content


def test_fetch_sentencia_raises_on_error(httpx_mock):
    from data.scripts.scrape_sentencias import fetch_sentencia

    httpx_mock.add_response(status_code=500)

    with pytest.raises(Exception):
        fetch_sentencia(SOURCE_URL, Path("/tmp/ignored.html"))
