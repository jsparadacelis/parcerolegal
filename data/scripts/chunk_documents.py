import json
import re
from datetime import datetime, timezone
from pathlib import Path

CONSTITUCION_PATH = Path("data/processed/constitucion.json")
SENTENCIAS_DIR = Path("data/processed/sentencias")
OUTPUT_PATH = Path("data/processed/chunks.json")

CHUNK_MAX = 1000
CHUNK_MIN = 800
OVERLAP = 150
MIN_CHUNK_LEN = 200

# Sentence boundary: after . ! ? followed by whitespace and uppercase letter
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ])")


def split_text(
    text: str,
    chunk_max: int = CHUNK_MAX,
    chunk_min: int = CHUNK_MIN,
    overlap: int = OVERLAP,
    min_chunk_len: int = MIN_CHUNK_LEN,
) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_max:
        return [text]

    # Find all sentence boundary positions
    boundaries = [m.start() for m in _SENTENCE_END_RE.finditer(text)]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        remaining = len(text) - start
        if remaining <= chunk_max:
            last_chunk = text[start:].strip()
            if last_chunk:
                chunks.append(last_chunk)
            break

        # Find the best sentence boundary in [chunk_min, chunk_max] from start
        cut = None
        for b in boundaries:
            pos = b - start
            if pos < chunk_min:
                continue
            if pos > chunk_max:
                break
            cut = b

        if cut is None:
            # Fallback: find last space within chunk_max
            window = text[start:start + chunk_max]
            space_pos = window.rfind(" ")
            if space_pos > min_chunk_len:
                cut = start + space_pos
            else:
                # Hard cut
                cut = start + chunk_max

        chunk = text[start:cut].strip()
        if chunk:
            chunks.append(chunk)

        # Next start with overlap, snapped to word boundary
        next_start = cut - overlap
        if next_start <= start:
            next_start = cut  # Avoid infinite loop
        else:
            # Snap forward to next space to avoid mid-word start
            space = text.find(" ", next_start)
            if space != -1 and space < cut:
                next_start = space + 1
        start = next_start

    # Final check: if last chunk is too small, merge with previous
    if len(chunks) >= 2 and len(chunks[-1]) < min_chunk_len:
        merged = chunks[-2] + " " + chunks[-1]
        chunks = chunks[:-2] + [merged]

    return chunks


def chunk_constitucion(constitucion_path: Path) -> list[dict]:
    data = json.loads(constitucion_path.read_text(encoding="utf-8"))
    chunks: list[dict] = []

    for article in data["articles"]:
        text = article["texto"].strip()
        if not text:
            continue

        parts = split_text(text)
        for i, part in enumerate(parts):
            chunks.append({
                "chunk_id": f"constitucion_art_{article['numero']}_{i}",
                "text": part,
                "source_type": "constitucion",
                "article_numero": article["numero"],
                "titulo": article["titulo"],
                "capitulo": article.get("capitulo"),
                "url_original": article["url_original"],
            })

    return chunks


def chunk_sentencia(sentencia_path: Path) -> list[dict]:
    data = json.loads(sentencia_path.read_text(encoding="utf-8"))
    meta = data["metadata"]
    chunks: list[dict] = []

    for seccion_name, seccion_text in data["secciones"].items():
        text = seccion_text.strip()
        if not text:
            continue

        parts = split_text(text)
        for i, part in enumerate(parts):
            chunks.append({
                "chunk_id": f"sentencia_{meta['sentencia_id']}_{seccion_name}_{i}",
                "text": part,
                "source_type": "sentencia",
                "sentencia_id": meta["sentencia_id"],
                "tipo": meta["tipo"],
                "year": meta["year"],
                "tema": meta["tema"],
                "seccion": seccion_name,
                "source_url": meta["source_url"],
            })

    return chunks


def chunk_all_sentencias(sentencias_dir: Path) -> list[dict]:
    chunks: list[dict] = []
    for path in sorted(sentencias_dir.glob("*.json")):
        chunks.extend(chunk_sentencia(path))
    return chunks


def build_output(constitucion_chunks: list[dict], sentencia_chunks: list[dict]) -> dict:
    all_chunks = constitucion_chunks + sentencia_chunks
    return {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_chunks": len(all_chunks),
            "sources": {
                "constitucion": len(constitucion_chunks),
                "sentencias": len(sentencia_chunks),
            },
        },
        "chunks": all_chunks,
    }


def main() -> None:
    print("Chunking constitución...")
    const_chunks = chunk_constitucion(CONSTITUCION_PATH)
    print(f"  {len(const_chunks)} chunks de constitución")

    print("Chunking sentencias...")
    sent_chunks = chunk_all_sentencias(SENTENCIAS_DIR)
    print(f"  {len(sent_chunks)} chunks de sentencias")

    output = build_output(const_chunks, sent_chunks)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n✓ {output['metadata']['total_chunks']} chunks totales → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
