import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# load_chunks
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_chunks_file(tmp_path):
    data = {
        "metadata": {"total_chunks": 3, "sources": {"constitucion": 2, "sentencias": 1}},
        "chunks": [
            {"chunk_id": "constitucion_art_1_0", "text": "Artículo 1. Colombia es un Estado social de derecho.", "source_type": "constitucion", "article_numero": 1, "titulo": "TITULO I", "capitulo": None, "url_original": "https://example.com#1"},
            {"chunk_id": "constitucion_art_2_0", "text": "Artículo 2. Son fines esenciales del Estado.", "source_type": "constitucion", "article_numero": 2, "titulo": "TITULO I", "capitulo": None, "url_original": "https://example.com#2"},
            {"chunk_id": "sentencia_T-999-23_antecedentes_0", "text": "El accionante presentó tutela contra la EPS.", "source_type": "sentencia", "sentencia_id": "T-999-23", "tipo": "T", "year": 2023, "tema": "Salud", "seccion": "antecedentes", "source_url": "https://example.com/T-999-23.htm"},
        ],
    }
    path = tmp_path / "chunks.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


class TestLoadChunks:
    def _load(self, path):
        from data.scripts.embed_and_upload import load_chunks
        return load_chunks(path)

    def test_returns_list_of_dicts(self, sample_chunks_file):
        chunks = self._load(sample_chunks_file)
        assert isinstance(chunks, list)
        assert len(chunks) == 3

    def test_each_chunk_has_text(self, sample_chunks_file):
        chunks = self._load(sample_chunks_file)
        for c in chunks:
            assert "text" in c
            assert "chunk_id" in c


# ---------------------------------------------------------------------------
# generate_embeddings
# ---------------------------------------------------------------------------


class TestGenerateEmbeddings:
    def test_returns_list_of_lists(self):
        from data.scripts.embed_and_upload import generate_embeddings

        texts = ["Hola mundo", "Derecho a la salud"]
        with patch("data.scripts.embed_and_upload.SentenceTransformer") as MockModel:
            import numpy as np
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.random.rand(2, 384).astype("float32")
            MockModel.return_value = mock_instance

            embeddings = generate_embeddings(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384

    def test_calls_model_encode(self):
        from data.scripts.embed_and_upload import generate_embeddings

        texts = ["Texto uno", "Texto dos", "Texto tres"]
        with patch("data.scripts.embed_and_upload.SentenceTransformer") as MockModel:
            import numpy as np
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.random.rand(3, 384).astype("float32")
            MockModel.return_value = mock_instance

            generate_embeddings(texts)

        mock_instance.encode.assert_called_once()


# ---------------------------------------------------------------------------
# build_payload
# ---------------------------------------------------------------------------


class TestBuildPayload:
    def _build(self, chunk):
        from data.scripts.embed_and_upload import build_payload
        return build_payload(chunk)

    def test_constitucion_payload(self):
        chunk = {
            "chunk_id": "constitucion_art_1_0",
            "text": "Artículo 1.",
            "source_type": "constitucion",
            "article_numero": 1,
            "titulo": "TITULO I",
            "capitulo": None,
            "url_original": "https://example.com#1",
        }
        payload = self._build(chunk)
        assert payload["source_type"] == "constitucion"
        assert payload["article_numero"] == 1
        assert payload["titulo"] == "TITULO I"
        assert "text" in payload

    def test_sentencia_payload(self):
        chunk = {
            "chunk_id": "sentencia_T-999-23_antecedentes_0",
            "text": "El accionante.",
            "source_type": "sentencia",
            "sentencia_id": "T-999-23",
            "tipo": "T",
            "year": 2023,
            "tema": "Salud",
            "seccion": "antecedentes",
            "source_url": "https://example.com",
        }
        payload = self._build(chunk)
        assert payload["source_type"] == "sentencia"
        assert payload["sentencia_id"] == "T-999-23"
        assert payload["seccion"] == "antecedentes"
        assert "text" in payload


# ---------------------------------------------------------------------------
# create_collection
# ---------------------------------------------------------------------------


class TestCreateCollection:
    def test_calls_recreate_collection(self):
        from data.scripts.embed_and_upload import create_collection

        mock_client = MagicMock()
        create_collection(mock_client, "test_collection")
        mock_client.recreate_collection.assert_called_once()

    def test_uses_384_dimensions_cosine(self):
        from data.scripts.embed_and_upload import create_collection
        from qdrant_client.models import Distance, VectorParams

        mock_client = MagicMock()
        create_collection(mock_client, "test_collection")

        call_kwargs = mock_client.recreate_collection.call_args
        vectors_config = call_kwargs.kwargs.get("vectors_config") or call_kwargs[1].get("vectors_config")
        assert vectors_config.size == 384
        assert vectors_config.distance == Distance.COSINE


# ---------------------------------------------------------------------------
# upload_batch
# ---------------------------------------------------------------------------


class TestUploadBatch:
    def test_calls_upsert(self):
        from data.scripts.embed_and_upload import upload_batch

        mock_client = MagicMock()
        chunks = [
            {"chunk_id": "c1", "text": "Hello", "source_type": "constitucion", "article_numero": 1, "titulo": "T", "capitulo": None, "url_original": "u"},
            {"chunk_id": "c2", "text": "World", "source_type": "constitucion", "article_numero": 2, "titulo": "T", "capitulo": None, "url_original": "u"},
        ]
        embeddings = [[0.1] * 384, [0.2] * 384]

        upload_batch(mock_client, "test", chunks, embeddings)
        mock_client.upsert.assert_called_once()

    def test_point_count_matches_chunks(self):
        from data.scripts.embed_and_upload import upload_batch

        mock_client = MagicMock()
        chunks = [
            {"chunk_id": f"c{i}", "text": f"Text {i}", "source_type": "constitucion", "article_numero": i, "titulo": "T", "capitulo": None, "url_original": "u"}
            for i in range(5)
        ]
        embeddings = [[0.1] * 384 for _ in range(5)]

        upload_batch(mock_client, "test", chunks, embeddings)

        call_kwargs = mock_client.upsert.call_args
        points = call_kwargs.kwargs.get("points") or call_kwargs[1].get("points")
        assert len(points) == 5
