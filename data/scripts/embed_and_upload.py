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

    return payload


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

    print(f"\nConectando a Qdrant...")
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
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
