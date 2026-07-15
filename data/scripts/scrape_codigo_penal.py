import json
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

SOURCE_URL = "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=6388"
RAW_PATH = Path("data/raw/codigo_penal.html")
OUTPUT_PATH = Path("data/processed/codigo_penal.json")

# Muchas adiciones posteriores a la Ley 599/2000 se numeran con sufijo (ej.
# "ARTÍCULO 103A.", "ARTÍCULO 134 A .", "ARTÍCULO 185a.", "ARTÍCULO 243-A",
# "ARTÍCULO 269-1" — este último con NÚMERO, no letra, tras un guion). El
# separador y la capitalización son inconsistentes en la fuente ("103A" pegado,
# "134 A" con espacio, "185a" minúscula, "243-A" con guion), así que se acepta
# con espacio/guion opcional antes y cualquier capitalización (ver IGNORECASE +
# _strong_text, que solo mira el <strong> del encabezado — ver su docstring para
# el bug real que motivó eso). Sin el grupo de sufijo, "103A"/"243-A"/"269-1" se
# truncarían a numero=103/243/269 y colisionarían con el artículo base real.
_ARTICLE_RE = re.compile(r"^ARTÍCULO\s+(\d+)(?:[\s-]*([A-Za-z0-9]+))?", re.IGNORECASE)
_LIBRO_RE = re.compile(r"^LIBRO\s+", re.IGNORECASE)
_TITULO_RE = re.compile(r"^T[IÍ]TULO\s+", re.IGNORECASE)
_CAPITULO_RE = re.compile(r"^CAP[IÍ]TULO\s+", re.IGNORECASE)
_NORMA_ANTERIOR_RE = re.compile(r"^(Norma Anterior|Texto Anterior)", re.IGNORECASE)
_NOTA_RE = re.compile(r"^Nota:", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")

# Libro II — Parte Especial — arranca en el Art. 101 (Ley 599 de 2000).
# Verificado contra el HTML fuente: LIBRO SEGUNDO precede directamente al Art. 101.
LIBRO_II_START_ARTICLE = 101


def fetch_page(url: str, raw_path: Path) -> str:
    response = httpx.get(url, verify=False, timeout=30)
    response.raise_for_status()

    html = response.text
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(html, encoding="utf-8")
    return html


def _clean(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _strong_text(tag) -> str:
    """Texto del <strong> de ENCABEZADO únicamente (el primero), no de todos los
    <strong> del párrafo. Descubierto contra HTML real: el cuerpo de algunos
    artículos trae énfasis judicial en <strong><u>...</u></strong> más adelante en
    el mismo <p> (ej. Art. 123, "...de la mujer <strong><u>o en mujer menor de
    catorce años</u></strong>..."); concatenar todos los <strong> hacía que esa
    'o' suelta se confundiera con un sufijo de letra del número de artículo."""
    strong = tag.find("strong")
    return _clean(strong.get_text()) if strong else ""


def _em_text(tag) -> str:
    em = tag.find("em")
    return _clean(em.get_text()) if em else ""


def _derive_nombre(bold_text: str, em_nombre: str, article_match: re.Match) -> str:
    """Nombre del delito: normalmente vive en <em> (ej. 'Homicidio'); en artículos
    con sufijo de letra a veces va dentro del propio <strong> junto al número
    (ej. '103A. Circunstancias De Agravación...'), sin <em>. Reutiliza el mismo
    match que identificó el artículo para no reconstruir a mano el prefijo
    'ARTÍCULO N[letra]' — su espaciado varía en la fuente ("103A" vs "134 A")."""
    if em_nombre:
        return em_nombre

    remainder = bold_text[article_match.end():].lstrip(". ").strip()
    return remainder.rstrip(".").strip()


def _is_centered_heading(tag) -> bool:
    return tag.get("align") == "center" and bool(tag.find("strong"))


def _save_article(articles: list[dict], article: dict | None) -> None:
    if article and article["numero"] >= LIBRO_II_START_ARTICLE:
        articles.append(article)


def parse_articles(html: str, source_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    div = soup.find("div", class_="descripcion-contenido")
    if not div:
        raise ValueError("No se encontró el div 'descripcion-contenido'")

    articles: list[dict] = []
    current_libro = ""
    current_titulo = ""
    current_capitulo = None
    current_article: dict | None = None
    in_norma_anterior = False
    # Los encabezados LIBRO/TÍTULO/CAPÍTULO llegan en dos (o más) <p> separados:
    # uno con el número ("TÍTULO VII") y el/los siguiente(s) con el nombre
    # ("DELITOS CONTRA EL PATRIMONIO ECONÓMICO"). Este flag recuerda a cuál
    # encabezado pertenece la próxima línea centrada.
    pending_heading: str | None = None

    for child in div.children:
        if not hasattr(child, "name") or child.name != "p":
            continue
        if child.find("button"):
            continue

        text = _clean(child.get_text(separator=" "))
        if not text:
            continue

        if _NORMA_ANTERIOR_RE.match(text):
            in_norma_anterior = True
            pending_heading = None
            continue

        if _NOTA_RE.match(text):
            continue

        bold_text = _strong_text(child)

        if _LIBRO_RE.match(bold_text) or _LIBRO_RE.match(text):
            _save_article(articles, current_article)
            current_article = None
            in_norma_anterior = False
            current_libro = text
            current_titulo = ""
            current_capitulo = None
            pending_heading = "libro"
            continue

        if _TITULO_RE.match(bold_text) or _TITULO_RE.match(text):
            _save_article(articles, current_article)
            current_article = None
            in_norma_anterior = False
            current_titulo = text
            current_capitulo = None
            pending_heading = "titulo"
            continue

        if _CAPITULO_RE.match(bold_text) or _CAPITULO_RE.match(text):
            _save_article(articles, current_article)
            current_article = None
            in_norma_anterior = False
            current_capitulo = text
            pending_heading = "capitulo"
            continue

        article_match = _ARTICLE_RE.match(bold_text)
        if article_match:
            _save_article(articles, current_article)
            in_norma_anterior = False
            pending_heading = None
            numero = int(article_match.group(1))
            sufijo = article_match.group(2).upper() if article_match.group(2) else None
            # Guion bajo como separador en el id: algunos sufijos son numéricos
            # (ej. "269-1"), así que "cp_art_2691" sería ambiguo con un
            # hipotético artículo 2691. "cp_art_269_1" no lo es.
            current_article = {
                "id": f"cp_art_{numero}" + (f"_{sufijo.lower()}" if sufijo else ""),
                "numero": numero,
                "sufijo": sufijo,
                "nombre": _derive_nombre(bold_text, _em_text(child), article_match),
                "libro": current_libro,
                "titulo": current_titulo,
                "capitulo": current_capitulo,
                "texto": text,
                "url_original": f"{source_url}#{numero}" + (f"-{sufijo}" if sufijo else ""),
            }
            continue

        if pending_heading and _is_centered_heading(child):
            if pending_heading == "libro":
                current_libro = f"{current_libro}. {text}"
            elif pending_heading == "titulo":
                current_titulo = f"{current_titulo}. {text}"
            elif pending_heading == "capitulo":
                current_capitulo = f"{current_capitulo}. {text}"
            continue

        pending_heading = None

        if in_norma_anterior:
            continue

        if current_article is not None:
            current_article["texto"] += " " + text

    _save_article(articles, current_article)

    for art in articles:
        art["texto"] = _strip_nombre_prefix(art["texto"], art["nombre"])

    return articles


def _strip_nombre_prefix(texto: str, nombre: str) -> str:
    """El texto crudo del <p> incluye 'ARTÍCULO N. Nombre . resto...'; nos quedamos
    solo con el cuerpo de la norma."""
    match = _ARTICLE_RE.match(texto)
    if not match:
        return texto
    remainder = texto[match.end():].lstrip(". ").strip()
    if nombre and remainder.lower().startswith(nombre.lower()):
        remainder = remainder[len(nombre):].lstrip(". ").strip()
    return remainder


def build_metadata(articles: list[dict], source_url: str) -> dict:
    return {
        "title": "Código Penal Colombiano (Ley 599 de 2000) — Libro II, Parte Especial",
        "source_url": source_url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "total_articles": len(articles),
    }


def main() -> None:
    print(f"Descargando desde {SOURCE_URL} ...")
    html = fetch_page(SOURCE_URL, RAW_PATH)

    articles = parse_articles(html, SOURCE_URL)
    meta = build_metadata(articles, SOURCE_URL)

    output = {"metadata": meta, "articles": articles}
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"✓ {meta['total_articles']} artículos (Libro II) → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
