import json
import os
import time
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

load_dotenv()

CHUNKS_PATH = Path("data/processed/chunks.json")
COLLECTION_NAME = "parcerolegal"
MODEL_NAME = "jina-embeddings-v3"
VECTOR_SIZE = 1024
BATCH_SIZE = 100
JINA_URL = "https://api.jina.ai/v1/embeddings"
MAX_RETRIES = 5
BASE_DELAY = 5.0


def load_chunks(chunks_path: Path) -> list[dict]:
    data = json.loads(chunks_path.read_text(encoding="utf-8"))
    return data["chunks"]


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    headers = {
        "Authorization": f"Bearer {os.getenv('JINA_API_KEY')}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "task": "retrieval.passage",
        "dimensions": VECTOR_SIZE,
        "input": texts,
    }

    for attempt in range(MAX_RETRIES):
        response = requests.post(JINA_URL, json=payload, headers=headers)
        if response.status_code == 429:
            time.sleep(BASE_DELAY * (2 ** attempt))
            continue
        response.raise_for_status()
        return [item["embedding"] for item in response.json()["data"]]

    response.raise_for_status()


def build_payload(chunk: dict) -> dict:
    payload = {"text": chunk["text"], "source_type": chunk["source_type"]}

    if chunk["source_type"] == "constitucion":
        payload["article_numero"] = chunk["article_numero"]
        payload["titulo"] = chunk["titulo"]
        payload["capitulo"] = chunk.get("capitulo")
        payload["url_original"] = chunk["url_original"]
    elif chunk["source_type"] == "sentencia":
        payload["sentencia_id"] = chunk["sentencia_id"]
        payload["tipo"] = chunk["tipo"]
        payload["year"] = chunk["year"]
        payload["tema"] = chunk["tema"]
        payload["seccion"] = chunk["seccion"]
        payload["source_url"] = chunk["source_url"]
    elif chunk["source_type"] == "codigo_penal":
        payload["article_id"] = chunk["article_id"]
        payload["article_numero"] = chunk["article_numero"]
        payload["sufijo"] = chunk.get("sufijo")
        payload["nombre"] = chunk.get("nombre")
        payload["titulo"] = chunk["titulo"]
        payload["capitulo"] = chunk.get("capitulo")
        payload["url_original"] = chunk["url_original"]
    elif chunk["source_type"] == "codigo_sustantivo_trabajo":
        payload["article_id"] = chunk["article_id"]
        payload["article_numero"] = chunk["article_numero"]
        payload["sufijo"] = chunk.get("sufijo")
        payload["nombre"] = chunk.get("nombre")
        payload["parte"] = chunk["parte"]
        payload["titulo"] = chunk["titulo"]
        payload["capitulo"] = chunk.get("capitulo")
        payload["url_original"] = chunk["url_original"]

    return payload


def filter_chunks_by_source_type(
    chunks: list[dict], source_types: set[str] | None
) -> list[dict]:
    """Permite un embed incremental (ej. solo 'codigo_penal' tras agregar el
    corpus nuevo) sin re-embeber chunks ya subidos. None = sin filtro."""
    if source_types is None:
        return chunks
    return [c for c in chunks if c["source_type"] in source_types]


def create_collection(client: QdrantClient, collection_name: str) -> None:
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    client.create_payload_index(
        collection_name=collection_name,
        field_name="sentencia_id",
        field_schema="keyword",
    )


def upload_batch(
    client: QdrantClient,
    collection_name: str,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> None:
    points = []
    for chunk, embedding in zip(chunks, embeddings):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk["chunk_id"]))
        payload = build_payload(chunk)
        points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

    client.upsert(collection_name=collection_name, points=points)


def main() -> None:
    print(f"Cargando chunks desde {CHUNKS_PATH}...")
    chunks = load_chunks(CHUNKS_PATH)
    print(f"  {len(chunks)} chunks cargados")

    source_types_env = os.getenv("EMBED_SOURCE_TYPES")
    if source_types_env:
        source_types = set(source_types_env.split(","))
        chunks = filter_chunks_by_source_type(chunks, source_types)
        print(f"  Filtrado a {source_types} → {len(chunks)} chunks")

    print(f"\nConectando a Qdrant...")
    # timeout=60: el default del cliente (5s) da WriteTimeout al subir batches de
    # 100 puntos × 1024 dims — el POST tarda más que eso en salir por esta red.
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=60,
    )

    if client.collection_exists(COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' ya existe, no se recrea.")
    else:
        print(f"Creando collection '{COLLECTION_NAME}'...")
        create_collection(client, COLLECTION_NAME)

    start_batch = int(os.getenv("START_BATCH", "0"))
    start_index = start_batch * BATCH_SIZE

    print(f"Generando embeddings con {MODEL_NAME} y subiendo en batches de {BATCH_SIZE} (desde batch {start_batch})...")
    for i in range(start_index, len(chunks), BATCH_SIZE):
        batch_chunks = chunks[i:i + BATCH_SIZE]
        batch_texts = [c["text"] for c in batch_chunks]
        batch_embeddings = generate_embeddings(batch_texts)
        upload_batch(client, COLLECTION_NAME, batch_chunks, batch_embeddings)
        print(f"  Batch {i // BATCH_SIZE + 1}: {len(batch_chunks)} puntos subidos")

    info = client.get_collection(COLLECTION_NAME)
    print(f"\n✓ Collection '{COLLECTION_NAME}': {info.points_count} puntos")


if __name__ == "__main__":
    main()
