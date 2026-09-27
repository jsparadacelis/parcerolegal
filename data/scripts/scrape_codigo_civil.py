import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# El gestor normativo de Función Pública (fuente de Constitución, CP y CST) responde
# "No disponible" para el Código Civil (norma.php?i=39535 redirige a norma_error.php,
# verificado 2026-09-27). La Secretaría del Senado publica el texto completo y
# actualizado, partido en ~84 páginas encadenadas por enlaces "Siguiente".
SOURCE_URL = "http://www.secretariasenado.gov.co/senado/basedoc/codigo_civil.html"
RAW_DIR = Path("data/raw/codigo_civil")
OUTPUT_PATH = Path("data/processed/codigo_civil.json")

# La página declara ISO-8859-1 y no trae bytes del rango 0x80-0x9F de cp1252.
_SOURCE_ENCODING = "latin-1"

# "1o." (ordinal de los Arts. 1-9) no es sufijo; un sufijo real sería "1781A." —
# se exige el punto inmediato para no confundir "ARTÍCULO 12 DE ..." con un "12D".
_ARTICLE_RE = re.compile(r"^ART[IÍ]CULO\.?\s+(\d+)(?:o|º)?(?:[\s-]?([A-Z])(?=\.))?")
_LIBRO_RE = re.compile(r"^LIBRO\b", re.IGNORECASE)
_TITULO_RE = re.compile(r"^T[IÍ]TULO\b", re.IGNORECASE)
_CAPITULO_RE = re.compile(r"^CAP[IÍ]TULO\b", re.IGNORECASE)
# Subdivisión propia del Código Civil ("PARAGRAFO 1o. DEL DIVORCIO") por debajo del
# capítulo: se reconoce solo para que su nombre no se pegue al capítulo vigente.
_PARAGRAFO_RE = re.compile(r"^PAR[AÁ]GRAFO\b", re.IGNORECASE)
# Pie de página repetido al final de cada una de las ~84 páginas.
_COPYRIGHT_RE = re.compile(r"^Las notas de vigencia, concordancias", re.IGNORECASE)
# Todo lo encerrado entre <...> lo agregó el editor, según aclara la propia fuente.
# Dos usos: notas ("<Ver Notas del Editor>", "<Artículo modificado por ...>"), que
# empiezan en mayúscula y no son norma; y reemplazos de un término tachado por el
# vigente ("Los <empleadores> [tachado: amos]"), en minúscula, que SÍ son norma.
_EDITOR_BRACKET_RE = re.compile(r"<([^<>]*)>")
_EDITOR_MARKS_TO_DROP = {"sic", "..."}
# Nota que la fuente abre y nunca cierra ("<Inciso primero derogado por ...").
_UNCLOSED_NOTE_RE = re.compile(r"^<[^>]*$")
_SPACE_BEFORE_PUNCTUATION_RE = re.compile(r"\s+([.,;:])")
_ANGLE_NOMBRE_RE = re.compile(r"^<([^<>]*)>")
_PLAIN_NOMBRE_RE = re.compile(r"^([^<.]+)\.")
_WHITESPACE_RE = re.compile(r"\s+")


def _page_name(url: str) -> str:
    return Path(urlparse(url).path).name


def _download(url: str, raw_path: Path) -> bytes:
    response = httpx.get(url, timeout=60, follow_redirects=True)
    response.raise_for_status()
    raw_path.write_bytes(response.content)
    return response.content


def _load_or_download(url: str, raw_dir: Path) -> str:
    raw_path = raw_dir / _page_name(url)
    raw_bytes = raw_path.read_bytes() if raw_path.exists() else _download(url, raw_path)
    return raw_bytes.decode(_SOURCE_ENCODING)


def _next_page_url(current_url: str, html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    for link in soup.find_all("a", class_="antsig"):
        if link.get_text(strip=True) == "Siguiente":
            return urljoin(current_url, link["href"])
    return None


def fetch_pages(first_url: str, raw_dir: Path) -> list[tuple[str, str]]:
    """Recorre la cadena de páginas "Siguiente" desde first_url. Cada página se
    cachea en raw_dir y, si ya está ahí, se lee del disco sin tocar la red."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    pages: list[tuple[str, str]] = []
    page_url: str | None = first_url
    while page_url:
        html = _load_or_download(page_url, raw_dir)
        pages.append((page_url, html))
        page_url = _next_page_url(page_url, html)
    return pages


def _clean(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _paragraph_text(paragraph) -> str:
    # separator="" porque el anchor corta palabras en la fuente ("<a>A</a>RTÍCULO 410").
    for line_break in paragraph.find_all("br"):
        line_break.replace_with(" ")
    return _clean(paragraph.get_text(separator=""))


def _is_uppercase_heading(text: str) -> bool:
    return any(char.isalpha() for char in text) and text == text.upper()


def _heading_label(text: str) -> str:
    return text.rstrip(". ").strip()


def _split_nombre(header_remainder: str) -> tuple[str, str]:
    """Separa el nombre del artículo del cuerpo. La fuente usa dos formas:
    'ARTÍCULO 33. <NOMBRE DEL EDITOR>. cuerpo' y, en artículos reformados
    recientemente, 'ARTÍCULO 156. NOMBRE OFICIAL. <nota> cuerpo'. Una nota en
    minúsculas ('<Artículo derogado ...>') no es nombre."""
    angle_match = _ANGLE_NOMBRE_RE.match(header_remainder)
    if angle_match:
        if _is_uppercase_heading(angle_match.group(1)):
            return angle_match.group(1).rstrip(". "), header_remainder[angle_match.end():]
        return "", header_remainder

    plain_match = _PLAIN_NOMBRE_RE.match(header_remainder)
    if plain_match and _is_uppercase_heading(plain_match.group(1)):
        return plain_match.group(1).strip(), header_remainder[plain_match.end():]
    return "", header_remainder


def _resolve_editor_bracket(bracket_match: re.Match) -> str:
    content = bracket_match.group(1).strip()
    if content[:1].islower() and content not in _EDITOR_MARKS_TO_DROP:
        return f" {content} "
    return " "


def _finalize_texto(raw_texto: str) -> str:
    without_notes = _EDITOR_BRACKET_RE.sub(_resolve_editor_bracket, raw_texto)
    # Los asteriscos remiten a notas del editor ("veintiún* años").
    without_footnote_marks = without_notes.replace("*", "")
    # Quitar apartes tachados deja huecos antes de la puntuación ("sus trabajadores ,").
    tightened = _SPACE_BEFORE_PUNCTUATION_RE.sub(r"\1", _clean(without_footnote_marks))
    return tightened.lstrip(". ").strip()


def _split_nombre_from_anchor(paragraph, text: str) -> tuple[str, str] | None:
    """El anchor <a name="N"> delimita el encabezado aun cuando el editor dejó el
    '<' del nombre sin cerrar ('<TRANSMISIBILIDAD DE LA FIANZA') o anidó un
    reemplazo ('<DAÑOS CAUSADOS POR LOS <TRABAJADORES>.'). No sirve cuando el
    anchor corta el encabezado ('<a>ARTÍCULO</a> 143.'): ahí devuelve None."""
    anchor = paragraph.find("a", attrs={"name": True})
    if anchor is None:
        return None
    anchor_text = _clean(anchor.get_text(separator=""))
    anchor_match = _ARTICLE_RE.match(anchor_text)
    if not anchor_match or not text.startswith(anchor_text):
        return None
    nombre = anchor_text[anchor_match.end():].replace("<", "").replace(">", "").strip(". ")
    if not _is_uppercase_heading(nombre):
        return None
    # Un '<' al final del anchor abre la nota siguiente ('...LEY>.<</a>Ver Notas...>'):
    # se deja en el cuerpo para que la nota se elimine completa.
    return nombre, text[len(anchor_text.rstrip("<")):]


def _new_article(
    article_match: re.Match, paragraph, text: str, page_url: str, hierarchy: dict
) -> dict:
    numero = int(article_match.group(1))
    sufijo = article_match.group(2)
    header_remainder = text[article_match.end():].lstrip(". ").strip()
    nombre, body = _split_nombre_from_anchor(paragraph, text) or _split_nombre(header_remainder)
    return {
        "id": f"cc_art_{numero}" + (f"_{sufijo.lower()}" if sufijo else ""),
        "numero": numero,
        "sufijo": sufijo,
        "nombre": nombre,
        "libro": hierarchy["libro"],
        "titulo": hierarchy["titulo"],
        "capitulo": hierarchy["capitulo"],
        "texto": body,
        "url_original": f"{page_url}#{numero}{sufijo or ''}",
    }


def _save_article(articles: list[dict], article: dict | None) -> None:
    if article:
        article["texto"] = _finalize_texto(article["texto"])
        articles.append(article)


def _apply_heading(hierarchy: dict, text: str) -> bool:
    """Actualiza la jerarquía si text es un rótulo LIBRO/TÍTULO/CAPÍTULO/PARÁGRAFO.
    El nombre del nivel llega en la(s) línea(s) centrada(s) siguiente(s)."""
    label = _heading_label(text)
    if _LIBRO_RE.match(text):
        hierarchy.update(libro=label, titulo=None, capitulo=None, pending="libro")
    elif _TITULO_RE.match(text):
        hierarchy.update(titulo=label, capitulo=None, pending="titulo")
    elif _CAPITULO_RE.match(text):
        hierarchy.update(capitulo=label, pending="capitulo")
    elif _PARAGRAFO_RE.match(text):
        hierarchy.update(pending="paragrafo")
    else:
        return False
    return True


def _apply_heading_name(hierarchy: dict, text: str) -> None:
    pending = hierarchy["pending"]
    if text.startswith("<"):
        # Nota del editor centrada bajo un título ("<NOTA DE VIGENCIA: ...>"), a
        # veces partida en dos líneas: corta la captura del nombre.
        hierarchy["pending"] = None
    elif pending in ("libro", "titulo", "capitulo"):
        hierarchy[pending] = f"{hierarchy[pending]}. {_heading_label(text)}"


def parse_articles(pages: list[tuple[str, str]]) -> list[dict]:
    articles: list[dict] = []
    hierarchy = {"libro": None, "titulo": None, "capitulo": None, "pending": None}
    current_article: dict | None = None

    for page_url, html in pages:
        soup = BeautifulSoup(html, "lxml")
        # <S> marca apartes tachados (declarados INEXEQUIBLES o derogados).
        for struck in soup.find_all("s"):
            struck.decompose()

        for paragraph in soup.find_all("p"):
            if paragraph.find("a", class_="antsig"):
                continue
            text = _paragraph_text(paragraph)
            if not text or _COPYRIGHT_RE.match(text):
                continue

            # Ninguna línea centrada es cuerpo de artículo (verificado contra las 84
            # páginas): son rótulos, subtítulos sueltos o las firmas finales.
            if "centrado" in (paragraph.get("class") or []):
                _save_article(articles, current_article)
                current_article = None
                if not _apply_heading(hierarchy, text):
                    _apply_heading_name(hierarchy, text)
                continue

            article_match = _ARTICLE_RE.match(text)
            if article_match:
                _save_article(articles, current_article)
                hierarchy["pending"] = None
                current_article = _new_article(
                    article_match, paragraph, text, page_url, hierarchy
                )
                continue

            if _UNCLOSED_NOTE_RE.match(text):
                continue

            if current_article is not None:
                current_article["texto"] += " " + text

    _save_article(articles, current_article)

    if not articles:
        raise ValueError("No se encontraron artículos en las páginas del Código Civil")
    return articles


def build_metadata(articles: list[dict], source_url: str) -> dict:
    return {
        "title": "Código Civil (Ley 84 de 1873, adoptado por la Ley 57 de 1887)",
        "source_url": source_url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "total_articles": len(articles),
        "articles_with_texto": sum(1 for art in articles if art["texto"]),
    }


def main() -> None:
    print(f"Leyendo páginas desde {SOURCE_URL} (caché en {RAW_DIR}) ...")
    pages = fetch_pages(SOURCE_URL, RAW_DIR)

    articles = parse_articles(pages)
    meta = build_metadata(articles, SOURCE_URL)

    output = {"metadata": meta, "articles": articles}
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"✓ {meta['total_articles']} artículos ({meta['articles_with_texto']} con texto, "
        f"{len(pages)} páginas) → {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
