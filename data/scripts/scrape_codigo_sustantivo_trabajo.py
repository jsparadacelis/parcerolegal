import json
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

SOURCE_URL = "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=199983"
RAW_PATH = Path("data/raw/codigo_sustantivo_trabajo.html")
OUTPUT_PATH = Path("data/processed/codigo_sustantivo_trabajo.json")

# Mismo patrón de sufijo inconsistente que Código Penal ("103A", "134 A", "243-A",
# "269-1"): aquí aparece como "97A", "185A", "235A", "241A", "391-1", "416A". Sin el
# grupo de sufijo, "97A" truncaría a numero=97 y colisionaría con el Art. 97 real.
_ARTICLE_RE = re.compile(r"^ART[IÍ]CULO\.?\s+(\d+)(?:[\s-]*([A-Za-z0-9]+))?", re.IGNORECASE)
# La Primera Parte no tiene rótulo propio en la fuente (arranca directo en "TITULO
# PRELIMINAR"); Segunda y Tercera Parte sí están rotuladas como "SEGUNDA PARTE." /
# "TERCERA PARTE." (orden invertido respecto al "PARTE GENERAL" del Código Penal).
_PARTE_RE = re.compile(r"^(PRIMERA|SEGUNDA|TERCERA)\s+PARTE", re.IGNORECASE)
_TITULO_RE = re.compile(r"^T[IÍ]TULO\s+", re.IGNORECASE)
_CAPITULO_RE = re.compile(r"^CAP[IÍ]TULO\s+", re.IGNORECASE)
_NORMA_ANTERIOR_RE = re.compile(r"^(Norma Anterior|Texto Anterior)", re.IGNORECASE)
# A diferencia de Código Penal (anotaciones con prefijo "Nota:"), aquí las notas de
# historia/jurisprudencia son párrafos que arrancan entre paréntesis: "(Modificado
# por el Art. X de la Ley Y)", "(Literal c) declarado EXEQUIBLE...)". Se descartan
# enteros — no son parte del texto vigente de la norma.
#
# No se exige que el paréntesis cierre: varias de estas anotaciones en el HTML real
# están mal formadas en la propia fuente y jamás cierran (ej. "(Modificado por el
# Art. 8 de la Ley 50 de 1990" sin ")" en ningún lado del <p>). Detectar solo por la
# palabra clave inicial, en vez de exigir el cierre, evita que esas anotaciones
# malformadas se cuelen como texto del artículo. Se acota a un paréntesis + palabra
# clave conocida (no "cualquier párrafo que empiece con paréntesis") para no
# descartar contenido normativo real que por estilo también abre con "(" — ej. la
# tabla de clasificación de invalidez (Art. 209) tiene cláusulas legítimas como
# "(La pérdida de un segmento de la falange ungueal solo se asimila...)".
_PARENTHETICAL_ANNOTATION_RE = re.compile(
    r"^\(\s*("
    r"Mod\.?\b|Modificad|Subrogad|Adicionad|Derogad|Corregid|Aclarad|Declarad|"
    r"Art[ií]culo\s+declarad|Apartes?|El\s+aparte|Literal\s|Numeral\s|Inciso|"
    r"Par[aá]grafo|El\s+texto\s+subrayado|Expresi[oó]n"
    r")",
    re.IGNORECASE,
)
# Caso real (Segunda Parte, Pactos Colectivos, Art. 70 de la Ley 50/1990): un
# artículo "adicionado" sin número formal en esta fuente, cuyo encabezado llega
# partido en dos <strong> consecutivos ("AR" + "TÍCULO. PROHIBICIÓN"). _strong_text
# solo mira el primer <strong> (ver su docstring), así que ese caso no matchea
# _ARTICLE_RE — sin este chequeo aparte, su cuerpo se fusionaría silenciosamente en
# el artículo anterior. Se descarta entero: hueco consciente, no se le inventa numeración.
_BROKEN_ARTICLE_RE = re.compile(r"^AR\s*T[IÍ]CULO\.?\s*(?!\d)", re.IGNORECASE)
# Placeholder sin resolver en la fuente (116 ocurrencias en el HTML real): parece un
# template de sustitución histórica "patrono→empleador" que no se resolvió. Se limpia
# quitando las llaves y dejando la palabra.
_PLACEHOLDER_BRACE_RE = re.compile(r"\{([^{}]+)\}")
_WHITESPACE_RE = re.compile(r"\s+")

_DEFAULT_PARTE = "PRIMERA PARTE. DERECHO INDIVIDUAL DEL TRABAJO"


def fetch_page(url: str, raw_path: Path) -> str:
    response = httpx.get(url, verify=False, timeout=30)
    response.raise_for_status()

    html = response.text
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(html, encoding="utf-8")
    return html


def _clean(text: str) -> str:
    cleaned = _WHITESPACE_RE.sub(" ", text).strip()
    return _PLACEHOLDER_BRACE_RE.sub(r"\1", cleaned)


def _strong_text(tag) -> str:
    """Texto del <strong> de ENCABEZADO únicamente (el primero), no de todos los
    <strong> del párrafo — mismo motivo que en Código Penal (evitar que un énfasis
    judicial posterior en el cuerpo se confunda con el encabezado)."""
    strong = tag.find("strong")
    return _clean(strong.get_text()) if strong else ""


def _all_strong_text(tag) -> str:
    """Concatena TODOS los <strong> del párrafo — solo para detectar el caso del
    artículo sin número partido en dos <strong> consecutivos (ver _BROKEN_ARTICLE_RE)."""
    return _clean(" ".join(s.get_text() for s in tag.find_all("strong")))


def _derive_nombre(bold_text: str, article_match: re.Match) -> str:
    """A diferencia de Código Penal (el nombre del delito vive en <em>), en el CST
    el nombre del artículo vive completo dentro del <strong> de encabezado (ej.
    'ARTICULO 391-1. DIRECTIVAS SECCIONALES.'). Un <em> SÍ aparece en el HTML real,
    pero como énfasis dentro del cuerpo (ej. Art. 391-1: 'Todo sindicato... <em>en
    aquellos municipios...</em>'), no como marcador de título — usarlo como fuente
    del nombre confundiría ese énfasis con el título real. Verificado contra el
    HTML completo: de 487 artículos, ninguno depende de <em> para su nombre."""
    remainder = bold_text[article_match.end():].lstrip(". ").strip()
    return remainder.rstrip(".").strip()


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
    current_parte = _DEFAULT_PARTE
    current_titulo = ""
    current_capitulo = None
    current_article: dict | None = None
    in_norma_anterior = False
    # Los encabezados PARTE/TÍTULO/CAPÍTULO llegan en dos (o más) <p> separados: uno
    # con el número ("TITULO VIII.") y el/los siguiente(s) con el nombre
    # ("TERMINACION DEL CONTRATO DE TRABAJO."). Este flag recuerda a cuál
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

        if _PARENTHETICAL_ANNOTATION_RE.match(text):
            continue

        bold_text = _strong_text(child)

        if _PARTE_RE.match(bold_text) or _PARTE_RE.match(text):
            _save_article(articles, current_article)
            current_article = None
            in_norma_anterior = False
            current_parte = text
            current_titulo = ""
            current_capitulo = None
            pending_heading = "parte"
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
            current_article = {
                "id": f"cst_art_{numero}" + (f"_{sufijo.lower()}" if sufijo else ""),
                "numero": numero,
                "sufijo": sufijo,
                "nombre": _derive_nombre(bold_text, article_match),
                "parte": current_parte,
                "titulo": current_titulo,
                "capitulo": current_capitulo,
                "texto": text,
                "url_original": f"{source_url}#{numero}" + (f"-{sufijo}" if sufijo else ""),
            }
            continue

        if _BROKEN_ARTICLE_RE.match(_all_strong_text(child)):
            _save_article(articles, current_article)
            current_article = None
            in_norma_anterior = False
            pending_heading = None
            continue

        if pending_heading and _is_centered_heading(child):
            if pending_heading == "parte":
                current_parte = f"{current_parte}. {text}"
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
    """El texto crudo del <p> incluye 'ARTICULO N. Nombre. resto...'; nos quedamos
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
        "title": "Código Sustantivo del Trabajo (Decreto 2663 de 1950)",
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
    print(f"✓ {meta['total_articles']} artículos (CST completo) → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
