import json
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

_WHITESPACE_RE = re.compile(r"\s+")
_NBSP_RE = re.compile(r"[\xa0\ufffd]+")

RAW_DIR = Path("data/raw/sentencias")
OUTPUT_DIR = Path("data/processed/sentencias")

SENTENCIAS_LIST = [
    # Batch 1
    {"id": "T-760-08", "url": "https://www.corteconstitucional.gov.co/relatoria/2008/T-760-08.htm", "tema": "Derecho a la salud"},
    {"id": "C-355-06", "url": "https://www.corteconstitucional.gov.co/relatoria/2006/C-355-06.htm", "tema": "Despenalización parcial aborto"},
    {"id": "SU-214-16", "url": "https://www.corteconstitucional.gov.co/relatoria/2016/su214-16.htm", "tema": "Matrimonio igualitario"},
    {"id": "T-025-04", "url": "https://www.corteconstitucional.gov.co/relatoria/2004/T-025-04.htm", "tema": "Desplazamiento forzado"},
    {"id": "T-406-92", "url": "https://www.corteconstitucional.gov.co/relatoria/1992/T-406-92.htm", "tema": "Estado social de derecho"},
    # Batch 2
    {"id": "C-221-94", "url": "https://www.corteconstitucional.gov.co/relatoria/1994/C-221-94.htm", "tema": "Dosis personal"},
    {"id": "C-239-97", "url": "https://www.corteconstitucional.gov.co/relatoria/1997/C-239-97.htm", "tema": "Eutanasia"},
    {"id": "T-881-02", "url": "https://www.corteconstitucional.gov.co/relatoria/2002/T-881-02.htm", "tema": "Dignidad humana"},
    {"id": "C-577-11", "url": "https://www.corteconstitucional.gov.co/relatoria/2011/C-577-11.htm", "tema": "Parejas del mismo sexo"},
    {"id": "T-398-19", "url": "https://www.corteconstitucional.gov.co/relatoria/2019/T-398-19.htm", "tema": "Libertad de expresión"},
]

# Section heading patterns — match Roman numerals or keywords
_SECTION_PREFIX = r"^[\dIVXivx]{0,5}[.\-\s]*"
_ANTECEDENTES_RE = re.compile(
    _SECTION_PREFIX + r"ANTECEDENTES", re.IGNORECASE
)
_CONSIDERACIONES_RE = re.compile(
    _SECTION_PREFIX + r"CONSIDERACIONES", re.IGNORECASE
)
_RESUELVE_RE = re.compile(r"^RESUELVE$", re.IGNORECASE)
_DECISION_RE = re.compile(
    _SECTION_PREFIX + r"DECISI[OÓ]N", re.IGNORECASE
)


def _parse_sentencia_id(sentencia_id: str) -> tuple[str, str, int]:
    """Parse 'T-760-08' into (tipo='T', numero='760', year=2008)."""
    parts = sentencia_id.split("-")
    tipo = parts[0]
    numero = parts[1]
    year_short = int(parts[2])
    year = year_short + 2000 if year_short < 50 else year_short + 1900
    return tipo, numero, year


def fetch_sentencia(url: str, raw_path: Path) -> str:
    response = httpx.get(url, verify=False, timeout=60)
    response.raise_for_status()

    # Most sentencias are encoded as windows-1252 but declared as such in meta
    # httpx may misdetect encoding; try windows-1252 first for Latin chars
    raw_bytes = response.content
    try:
        html = raw_bytes.decode("windows-1252")
    except (UnicodeDecodeError, LookupError):
        html = response.text

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(html, encoding="utf-8")
    return html


def clean_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator=" ")
    text = _NBSP_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _get_section1(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "lxml")
    section = soup.find("div", class_="Section1")
    if section:
        return section
    return soup


def _tag_text(tag) -> str:
    """Get clean text from a tag."""
    text = tag.get_text(separator=" ")
    text = _NBSP_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _heading_text(tag) -> str:
    """Get the heading text — from bold children or the tag itself for h1-h6."""
    if tag.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return _tag_text(tag)
    bold = tag.find(["b", "strong"])
    if bold:
        return _tag_text(bold)
    return ""


def parse_metadata(html: str, sentencia_id: str, source_url: str) -> dict:
    tipo, numero, year = _parse_sentencia_id(sentencia_id)
    section = _get_section1(html)

    magistrado = ""
    fecha = ""
    tema = ""

    looking_for_magistrado_name = False

    for tag in section.find_all(["p", "h1", "h2", "h3"]):
        text = _tag_text(tag)
        if not text:
            continue

        # Magistrado Ponente — the name is usually on the next line
        if not magistrado and re.search(r"MAGISTRAD[OA]\s+PONENTE", text, re.IGNORECASE):
            # Sometimes name is on the same line after a colon
            match = re.search(r"PONENTE[:\s]+(?:Dr\.?\s+)?(.+)", text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 3:
                    magistrado = name
                else:
                    looking_for_magistrado_name = True
            else:
                looking_for_magistrado_name = True
            continue

        if looking_for_magistrado_name:
            # The next non-empty paragraph with bold text is the name
            bold = tag.find(["b", "strong"])
            if bold:
                magistrado = _tag_text(bold)
            else:
                magistrado = text
            looking_for_magistrado_name = False
            continue

        # Fecha — "Bogotá, D.C., ..."
        if re.match(r"(Bogot|Santaf)", text, re.IGNORECASE) and not fecha:
            fecha = text
            continue

    # Extract tema from first bold descriptors (before metadata section)
    for tag in section.find_all(["p"], limit=10):
        bold = tag.find(["b", "strong"])
        if bold:
            bold_text = _tag_text(bold)
            # Skip the sentencia title line
            if re.match(r"Sentencia", bold_text, re.IGNORECASE):
                continue
            # Tema lines look like "DERECHO A LA SALUD-Acceso..."
            if "-" in bold_text and len(bold_text) > 5:
                tema = bold_text
                break

    # Find sentencia entry in SENTENCIAS_LIST for tema fallback
    for entry in SENTENCIAS_LIST:
        if entry["id"] == sentencia_id:
            if not tema:
                tema = entry["tema"]
            break

    return {
        "sentencia_id": sentencia_id,
        "tipo": tipo,
        "numero": numero,
        "year": year,
        "fecha": fecha,
        "magistrado_ponente": magistrado,
        "tema": tema,
        "source_url": source_url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def extract_sections(html: str) -> dict:
    section = _get_section1(html)
    tags = section.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"])

    current_section = None
    buffers = {
        "antecedentes": [],
        "consideraciones": [],
        "resuelve": [],
    }

    for tag in tags:
        text = _tag_text(tag)
        if not text:
            continue

        heading = _heading_text(tag)

        # Check if this is a section heading
        if _ANTECEDENTES_RE.search(heading) or _ANTECEDENTES_RE.search(text):
            current_section = "antecedentes"
            continue

        if _CONSIDERACIONES_RE.search(heading) or _CONSIDERACIONES_RE.search(text):
            current_section = "consideraciones"
            continue

        if _DECISION_RE.search(heading) or _DECISION_RE.search(text):
            current_section = "resuelve"
            continue

        if _RESUELVE_RE.search(heading) or _RESUELVE_RE.search(text):
            current_section = "resuelve"
            continue

        if current_section and current_section in buffers:
            buffers[current_section].append(text)

    return {
        "antecedentes": " ".join(buffers["antecedentes"]),
        "consideraciones": " ".join(buffers["consideraciones"]),
        "resuelve": " ".join(buffers["resuelve"]),
    }


def main(sentencias: list[dict] | None = None) -> None:
    if sentencias is None:
        sentencias = SENTENCIAS_LIST

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for entry in sentencias:
        sid = entry["id"]
        url = entry["url"]
        raw_path = RAW_DIR / f"{sid}.html"
        output_path = OUTPUT_DIR / f"{sid}.json"

        print(f"Descargando {sid} desde {url} ...")
        html = fetch_sentencia(url, raw_path)

        metadata = parse_metadata(html, sid, url)
        metadata["tema"] = entry["tema"]
        sections = extract_sections(html)
        texto_completo = clean_text(html)

        output = {
            "metadata": metadata,
            "secciones": sections,
            "texto_completo": texto_completo,
        }

        output_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"  ✓ {sid} → {output_path}")

    print(f"\n✓ {len(sentencias)} sentencias procesadas")


if __name__ == "__main__":
    import sys

    if "--id" in sys.argv:
        idx = sys.argv.index("--id") + 1
        target_id = sys.argv[idx]
        targets = [s for s in SENTENCIAS_LIST if s["id"] == target_id]
        if not targets:
            print(f"Sentencia {target_id} no encontrada en SENTENCIAS_LIST")
            sys.exit(1)
        main(targets)
    else:
        main()
