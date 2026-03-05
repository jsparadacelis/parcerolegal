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
