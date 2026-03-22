import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

load_dotenv()

CHUNKS_PATH = Path("data/processed/chunks.json")
COLLECTION_NAME = "parcerolegal"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_SIZE = 384
BATCH_SIZE = 100


def load_chunks(chunks_path: Path) -> list[dict]:
    data = json.loads(chunks_path.read_text(encoding="utf-8"))
    return data["chunks"]


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=BATCH_SIZE)
    return embeddings.tolist()


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

    print(f"\nGenerando embeddings con {MODEL_NAME}...")
    texts = [c["text"] for c in chunks]
    embeddings = generate_embeddings(texts)
    print(f"  {len(embeddings)} embeddings generados ({VECTOR_SIZE} dimensiones)")

    print(f"\nConectando a Qdrant...")
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )

    print(f"Creando collection '{COLLECTION_NAME}'...")
    create_collection(client, COLLECTION_NAME)

    print(f"Subiendo {len(chunks)} puntos en batches de {BATCH_SIZE}...")
    for i in range(0, len(chunks), BATCH_SIZE):
        batch_chunks = chunks[i:i + BATCH_SIZE]
        batch_embeddings = embeddings[i:i + BATCH_SIZE]
        upload_batch(client, COLLECTION_NAME, batch_chunks, batch_embeddings)
        print(f"  Batch {i // BATCH_SIZE + 1}: {len(batch_chunks)} puntos subidos")

    info = client.get_collection(COLLECTION_NAME)
    print(f"\n✓ Collection '{COLLECTION_NAME}': {info.points_count} puntos")


if __name__ == "__main__":
    main()
