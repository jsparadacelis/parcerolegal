"""Test queries against Qdrant to verify retrieval quality."""
import os
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

load_dotenv()

COLLECTION_NAME = "parcerolegal"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MIN_SCORE = 0.6
TOP_K = 5

TEST_QUERIES = [
    "¿Cuáles son los derechos fundamentales en Colombia?",
    "¿Qué dice la Constitución sobre el derecho a la salud?",
    "¿Qué es el matrimonio igualitario según la Corte Constitucional?",
    "¿Cuándo se puede despenalizar el aborto en Colombia?",
    "¿Qué derechos tienen las personas desplazadas?",
]


def main() -> None:
    print("Cargando modelo de embeddings...")
    model = SentenceTransformer(MODEL_NAME)

    print("Conectando a Qdrant...")
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )

    info = client.get_collection(COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}': {info.points_count} puntos\n")

    all_pass = True

    for query in TEST_QUERIES:
        print(f"Q: {query}")
        embedding = model.encode(query).tolist()

        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=embedding,
            limit=TOP_K,
        ).points

        if not results:
            print("  ❌ Sin resultados\n")
            all_pass = False
            continue

        top_score = results[0].score
        above_threshold = sum(1 for r in results if r.score >= MIN_SCORE)
        status = "✓" if top_score >= MIN_SCORE else "❌"

        print(f"  {status} Top score: {top_score:.4f} | {above_threshold}/{TOP_K} >= {MIN_SCORE}")

        for i, r in enumerate(results[:3]):
            p = r.payload
            source = p.get("source_type", "?")
            if source == "constitucion":
                label = f"Art. {p.get('article_numero')}"
            else:
                label = f"{p.get('sentencia_id')} ({p.get('seccion')})"
            print(f"    [{i+1}] {r.score:.4f} | {source}: {label} | {p['text'][:80]}...")

        print()

        if top_score < MIN_SCORE:
            all_pass = False

    if all_pass:
        print("✓ Todas las queries tienen al menos un resultado >= 0.6")
    else:
        print("❌ Algunas queries no alcanzaron el threshold de 0.6")


if __name__ == "__main__":
    main()
