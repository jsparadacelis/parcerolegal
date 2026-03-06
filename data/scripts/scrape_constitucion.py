import json
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

SOURCE_URL = "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4125"
RAW_PATH = Path("data/raw/constitucion.html")
OUTPUT_PATH = Path("data/processed/constitucion.json")

_ARTICLE_RE = re.compile(r"^ARTÍCULO\s+(\d+)", re.IGNORECASE)
_TRANSITORIO_RE = re.compile(r"TRANSITORIO", re.IGNORECASE)
_TITULO_RE = re.compile(r"^TITULO\s+", re.IGNORECASE)
_CAPITULO_RE = re.compile(r"^CAP[IÍ]TULO\s+", re.IGNORECASE)
_VER_RE = re.compile(r"^\(Ver\s", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")

# The HTML source omits most title/chapter headings, so we use a static map
# based on the official structure of the 1991 Constitution.
_STRUCTURE_MAP: list[tuple[int, int, str, str | None]] = [
    # (art_start, art_end, titulo, capitulo)
    (1, 10, "TITULO I. DE LOS PRINCIPIOS FUNDAMENTALES", None),
    (11, 41, "TITULO II. DE LOS DERECHOS, LAS GARANTIAS Y LOS DEBERES", "CAPITULO 1. De los Derechos Fundamentales"),
    (42, 77, "TITULO II. DE LOS DERECHOS, LAS GARANTIAS Y LOS DEBERES", "CAPITULO 2. De los Derechos Sociales, Económicos y Culturales"),
    (78, 82, "TITULO II. DE LOS DERECHOS, LAS GARANTIAS Y LOS DEBERES", "CAPITULO 3. De los Derechos Colectivos y del Ambiente"),
    (83, 94, "TITULO II. DE LOS DERECHOS, LAS GARANTIAS Y LOS DEBERES", "CAPITULO 4. De la Protección y Aplicación de los Derechos"),
    (95, 95, "TITULO II. DE LOS DERECHOS, LAS GARANTIAS Y LOS DEBERES", "CAPITULO 5. De los Deberes y Obligaciones"),
    (96, 100, "TITULO III. DE LOS HABITANTES Y DEL TERRITORIO", "CAPITULO 1. De la Nacionalidad"),
    (101, 102, "TITULO III. DE LOS HABITANTES Y DEL TERRITORIO", "CAPITULO 2. Del Territorio"),
    (103, 106, "TITULO IV. DE LA PARTICIPACION DEMOCRATICA Y DE LOS PARTIDOS POLITICOS", "CAPITULO 1. De las Formas de Participación Democrática"),
    (107, 112, "TITULO IV. DE LA PARTICIPACION DEMOCRATICA Y DE LOS PARTIDOS POLITICOS", "CAPITULO 2. De los Partidos y de los Movimientos Políticos"),
    (113, 113, "TITULO V. DE LA ORGANIZACION DEL ESTADO", "CAPITULO 1. De la Estructura del Estado"),
    (114, 120, "TITULO V. DE LA ORGANIZACION DEL ESTADO", "CAPITULO 2. De la Función Pública"),
    (121, 131, "TITULO V. DE LA ORGANIZACION DEL ESTADO", "CAPITULO 2. De la Función Pública"),
    (132, 137, "TITULO VI. DE LA RAMA LEGISLATIVA", "CAPITULO 1. De la Composición y las Funciones"),
    (138, 149, "TITULO VI. DE LA RAMA LEGISLATIVA", "CAPITULO 2. De la Reunión y el Funcionamiento"),
    (150, 170, "TITULO VI. DE LA RAMA LEGISLATIVA", "CAPITULO 3. De las Leyes"),
    (171, 175, "TITULO VI. DE LA RAMA LEGISLATIVA", "CAPITULO 4. Del Senado"),
    (176, 187, "TITULO VI. DE LA RAMA LEGISLATIVA", "CAPITULO 5. De la Cámara de Representantes"),
    (188, 199, "TITULO VII. DE LA RAMA EJECUTIVA", "CAPITULO 1. Del Presidente de la República"),
    (200, 201, "TITULO VII. DE LA RAMA EJECUTIVA", "CAPITULO 2. Del Gobierno"),
    (202, 205, "TITULO VII. DE LA RAMA EJECUTIVA", "CAPITULO 3. Del Vicepresidente"),
    (206, 208, "TITULO VII. DE LA RAMA EJECUTIVA", "CAPITULO 4. De los Ministros y Directores de Departamentos Administrativos"),
    (209, 211, "TITULO VII. DE LA RAMA EJECUTIVA", "CAPITULO 5. De la Función Administrativa"),
    (212, 215, "TITULO VII. DE LA RAMA EJECUTIVA", "CAPITULO 6. De los Estados de Excepción"),
    (216, 223, "TITULO VII. DE LA RAMA EJECUTIVA", "CAPITULO 7. De la Fuerza Pública"),
    (224, 227, "TITULO VII. DE LA RAMA EJECUTIVA", "CAPITULO 8. De las Relaciones Internacionales"),
    (228, 233, "TITULO VIII. DE LA RAMA JUDICIAL", "CAPITULO 1. Disposiciones Generales"),
    (234, 235, "TITULO VIII. DE LA RAMA JUDICIAL", "CAPITULO 2. De la Jurisdicción Ordinaria"),
    (236, 245, "TITULO VIII. DE LA RAMA JUDICIAL", "CAPITULO 3. De la Jurisdicción Contencioso Administrativa"),
    (239, 245, "TITULO VIII. DE LA RAMA JUDICIAL", "CAPITULO 4. De la Jurisdicción Constitucional"),
    (246, 248, "TITULO VIII. DE LA RAMA JUDICIAL", "CAPITULO 5. De las Jurisdicciones Especiales"),
    (249, 253, "TITULO VIII. DE LA RAMA JUDICIAL", "CAPITULO 6. De la Fiscalía General de la Nación"),
    (254, 257, "TITULO VIII. DE LA RAMA JUDICIAL", "CAPITULO 7. Del Consejo Superior de la Judicatura"),
    (258, 263, "TITULO IX. DE LAS ELECCIONES Y DE LA ORGANIZACION ELECTORAL", "CAPITULO 1. Del Sufragio y de las Elecciones"),
    (264, 266, "TITULO IX. DE LAS ELECCIONES Y DE LA ORGANIZACION ELECTORAL", "CAPITULO 2. De las Autoridades Electorales"),
    (267, 274, "TITULO X. DE LOS ORGANISMOS DE CONTROL", "CAPITULO 1. De la Contraloría General de la República"),
    (275, 284, "TITULO X. DE LOS ORGANISMOS DE CONTROL", "CAPITULO 2. Del Ministerio Público"),
    (285, 296, "TITULO XI. DE LA ORGANIZACION TERRITORIAL", "CAPITULO 1. De las Disposiciones Generales"),
    (297, 310, "TITULO XI. DE LA ORGANIZACION TERRITORIAL", "CAPITULO 2. Del Régimen Departamental"),
    (311, 321, "TITULO XI. DE LA ORGANIZACION TERRITORIAL", "CAPITULO 3. Del Régimen Municipal"),
    (322, 328, "TITULO XI. DE LA ORGANIZACION TERRITORIAL", "CAPITULO 4. Del Régimen Especial"),
    (329, 331, "TITULO XI. DE LA ORGANIZACION TERRITORIAL", "CAPITULO 5. Disposiciones Especiales"),
    (332, 338, "TITULO XII. DEL REGIMEN ECONOMICO Y DE LA HACIENDA PUBLICA", "CAPITULO 1. De las Disposiciones Generales"),
    (339, 344, "TITULO XII. DEL REGIMEN ECONOMICO Y DE LA HACIENDA PUBLICA", "CAPITULO 2. De los Planes de Desarrollo"),
    (345, 355, "TITULO XII. DEL REGIMEN ECONOMICO Y DE LA HACIENDA PUBLICA", "CAPITULO 3. Del Presupuesto"),
    (356, 364, "TITULO XII. DEL REGIMEN ECONOMICO Y DE LA HACIENDA PUBLICA", "CAPITULO 4. De la Distribución de Recursos y de las Competencias"),
    (365, 370, "TITULO XII. DEL REGIMEN ECONOMICO Y DE LA HACIENDA PUBLICA", "CAPITULO 5. De la Finalidad Social del Estado y de los Servicios Públicos"),
    (371, 373, "TITULO XII. DEL REGIMEN ECONOMICO Y DE LA HACIENDA PUBLICA", "CAPITULO 6. De la Banca Central"),
    (374, 380, "TITULO XIII. DE LA REFORMA DE LA CONSTITUCION", None),
]


def _lookup_structure(numero: int) -> tuple[str, str | None]:
    for start, end, titulo, capitulo in _STRUCTURE_MAP:
        if start <= numero <= end:
            return titulo, capitulo
    return "", None


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
    return " ".join(_clean(s.get_text()) for s in tag.find_all("strong"))


def _is_centered_heading(tag) -> bool:
    return tag.get("align") == "center" and bool(tag.find("strong"))


def _save_article(articles: list[dict], article: dict | None) -> None:
    if article:
        articles.append(article)


def parse_articles(html: str, source_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    div = soup.find("div", class_="descripcion-contenido")
    if not div:
        raise ValueError("No se encontró el div 'descripcion-contenido'")

    articles: list[dict] = []
    current_titulo = ""
    current_capitulo = None
    current_article: dict | None = None

    for child in div.children:
        if not hasattr(child, "name") or child.name != "p":
            continue
        if child.find("button"):
            continue

        text = _clean(child.get_text(separator=" "))
        if not text:
            continue
        if _VER_RE.match(text):
            continue

        bold_text = _strong_text(child)

        if _TITULO_RE.match(bold_text) or _TITULO_RE.match(text):
            _save_article(articles, current_article)
            current_article = None
            current_titulo = text
            current_capitulo = None
            continue

        if _CAPITULO_RE.match(bold_text) or _CAPITULO_RE.match(text):
            _save_article(articles, current_article)
            current_article = None
            current_capitulo = text
            continue

        if _is_centered_heading(child):
            _save_article(articles, current_article)
            current_article = None
            continue

        article_match = _ARTICLE_RE.match(bold_text) or _ARTICLE_RE.match(text)
        if article_match:
            is_transitorio = _TRANSITORIO_RE.search(bold_text) or _TRANSITORIO_RE.search(text)
            if is_transitorio:
                _save_article(articles, current_article)
                current_article = None
                continue

            _save_article(articles, current_article)
            numero = int(article_match.group(1))
            current_article = {
                "id": f"art_{numero}",
                "numero": numero,
                "titulo": current_titulo,
                "capitulo": current_capitulo,
                "texto": text,
                "url_original": f"{source_url}#{numero}",
            }
            continue

        if current_article is not None:
            current_article["texto"] += " " + text

    _save_article(articles, current_article)

    for art in articles:
        titulo, capitulo = _lookup_structure(art["numero"])
        art["titulo"] = titulo
        art["capitulo"] = capitulo

    return articles


def build_metadata(articles: list[dict], source_url: str) -> dict:
    return {
        "title": "Constitución Política de Colombia 1991",
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
    print(f"✓ {meta['total_articles']} artículos → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
