import json
import re
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# split_text
# ---------------------------------------------------------------------------


class TestSplitText:
    def _split(self, text, **kwargs):
        from data.scripts.chunk_documents import split_text
        return split_text(text, **kwargs)

    def test_short_text_returns_single_chunk(self):
        text = "Esta es una oración corta. Tiene menos de mil caracteres."
        chunks = self._split(text)
        assert chunks == [text]

    def test_long_text_returns_multiple_chunks(self):
        # ~2700 chars → should produce 3+ chunks
        sentences = ["Esta es la oración número %d del texto de prueba. " % i for i in range(60)]
        text = "".join(sentences)
        assert len(text) > 2500
        chunks = self._split(text)
        assert len(chunks) >= 3

    def test_chunks_within_size_limits(self):
        sentences = ["Oración de prueba número %d para verificar límites. " % i for i in range(60)]
        text = "".join(sentences)
        chunks = self._split(text)
        for i, chunk in enumerate(chunks):
            if i < len(chunks) - 1:
                assert len(chunk) <= 1000, f"Chunk {i} excede 1000 chars: {len(chunk)}"
                assert len(chunk) >= 200, f"Chunk {i} menor a 200 chars: {len(chunk)}"

    def test_overlap_present(self):
        sentences = ["Oración de prueba número %d en el texto. " % i for i in range(60)]
        text = "".join(sentences)
        chunks = self._split(text)
        assert len(chunks) >= 2
        # The end of chunk N should appear at the start of chunk N+1
        for i in range(len(chunks) - 1):
            tail = chunks[i][-100:]
            assert tail in chunks[i + 1], (
                f"Overlap no encontrado entre chunk {i} y {i+1}"
            )

    def test_splits_at_sentence_boundary(self):
        sentences = ["Oración número %d del documento legal. " % i for i in range(40)]
        text = "".join(sentences)
        chunks = self._split(text)
        for i, chunk in enumerate(chunks):
            if i < len(chunks) - 1:
                # Chunk should end at a sentence boundary (period, ?, !)
                stripped = chunk.rstrip()
                assert stripped[-1] in ".?!", (
                    f"Chunk {i} no termina en límite de oración: ...{stripped[-20:]}"
                )

    def test_discards_tiny_trailing_fragment(self):
        # Build text where the last fragment would be ~100 chars
        base = "A" * 900 + ". "
        tail = "Cola corta. "  # ~12 chars, well under 200
        text = base + base + tail
        chunks = self._split(text)
        # The tiny tail should be merged into the last chunk
        for chunk in chunks:
            assert len(chunk) >= 12  # at minimum the tail is included somewhere

    def test_no_content_lost(self):
        sentences = ["Frase número %d con contenido importante. " % i for i in range(50)]
        text = "".join(sentences)
        chunks = self._split(text)
        # Every sentence should appear in at least one chunk
        for sentence in sentences:
            found = any(sentence.strip() in chunk for chunk in chunks)
            assert found, f"Contenido perdido: {sentence[:50]}"

    def test_empty_text_returns_empty_list(self):
        assert self._split("") == []

    def test_whitespace_only_returns_empty_list(self):
        assert self._split("   ") == []

    def test_fallback_to_space_when_no_sentence_boundary(self):
        # Text with no periods — should split at spaces
        text = " ".join(["palabra"] * 300)  # ~2100 chars
        chunks = self._split(text)
        assert len(chunks) >= 2
        for chunk in chunks:
            # Should not cut mid-word
            assert not chunk.startswith("alabra"), "Chunk cortó a mitad de palabra"


# ---------------------------------------------------------------------------
# chunk_constitucion
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_constitucion(tmp_path):
    data = {
        "metadata": {
            "title": "Constitución Política de Colombia 1991",
            "source_url": "https://example.com",
            "total_articles": 3,
        },
        "articles": [
            {
                "id": "art_1",
                "numero": 1,
                "titulo": "TITULO I. DE LOS PRINCIPIOS FUNDAMENTALES",
                "capitulo": None,
                "texto": "ARTÍCULO 1. Colombia es un Estado social de derecho.",
                "url_original": "https://example.com#1",
            },
            {
                "id": "art_2",
                "numero": 2,
                "titulo": "TITULO I. DE LOS PRINCIPIOS FUNDAMENTALES",
                "capitulo": None,
                "texto": " ".join(
                    ["Oración %d del artículo largo sobre fines esenciales del Estado." % i for i in range(30)]
                ),
                "url_original": "https://example.com#2",
            },
            {
                "id": "art_11",
                "numero": 11,
                "titulo": "TITULO II. DE LOS DERECHOS",
                "capitulo": "CAPITULO 1. De los Derechos Fundamentales",
                "texto": "ARTÍCULO 11. El derecho a la vida es inviolable.",
                "url_original": "https://example.com#11",
            },
        ],
    }
    path = tmp_path / "constitucion.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


class TestChunkConstitucion:
    def _chunk(self, path):
        from data.scripts.chunk_documents import chunk_constitucion
        return chunk_constitucion(path)

    def test_returns_list_of_dicts(self, sample_constitucion):
        chunks = self._chunk(sample_constitucion)
        assert isinstance(chunks, list)
        assert all(isinstance(c, dict) for c in chunks)

    def test_chunk_has_required_fields(self, sample_constitucion):
        chunks = self._chunk(sample_constitucion)
        required = {"chunk_id", "text", "source_type", "article_numero", "titulo", "capitulo", "url_original"}
        for c in chunks:
            missing = required - c.keys()
            assert not missing, f"Chunk {c.get('chunk_id')} le faltan campos: {missing}"

    def test_source_type_is_constitucion(self, sample_constitucion):
        chunks = self._chunk(sample_constitucion)
        for c in chunks:
            assert c["source_type"] == "constitucion"

    def test_short_article_single_chunk(self, sample_constitucion):
        chunks = self._chunk(sample_constitucion)
        art1_chunks = [c for c in chunks if c["article_numero"] == 1]
        assert len(art1_chunks) == 1

    def test_long_article_multiple_chunks(self, sample_constitucion):
        chunks = self._chunk(sample_constitucion)
        art2_chunks = [c for c in chunks if c["article_numero"] == 2]
        assert len(art2_chunks) >= 2

    def test_chunk_id_format(self, sample_constitucion):
        chunks = self._chunk(sample_constitucion)
        pattern = re.compile(r"^constitucion_art_\d+_\d+$")
        for c in chunks:
            assert pattern.match(c["chunk_id"]), f"chunk_id inválido: {c['chunk_id']}"

    def test_preserves_article_metadata(self, sample_constitucion):
        chunks = self._chunk(sample_constitucion)
        art11 = [c for c in chunks if c["article_numero"] == 11]
        assert len(art11) == 1
        assert art11[0]["titulo"] == "TITULO II. DE LOS DERECHOS"
        assert art11[0]["capitulo"] == "CAPITULO 1. De los Derechos Fundamentales"
        assert art11[0]["url_original"] == "https://example.com#11"


# ---------------------------------------------------------------------------
# chunk_sentencia
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_sentencia(tmp_path):
    data = {
        "metadata": {
            "sentencia_id": "T-999-23",
            "tipo": "T",
            "numero": "999",
            "year": 2023,
            "fecha": "15 de marzo de 2023",
            "magistrado_ponente": "Diana Fajardo Rivera",
            "tema": "Derecho a la salud",
            "source_url": "https://example.com/T-999-23.htm",
            "scraped_at": "2026-03-22T00:00:00+00:00",
        },
        "secciones": {
            "antecedentes": "El accionante presentó tutela. " * 30,  # ~930 chars → 1 chunk
            "consideraciones": " ".join(
                ["Oración %d sobre consideraciones jurídicas del caso." % i for i in range(40)]
            ),  # ~2000 chars → 2+ chunks
            "resuelve": "",  # empty — should be skipped
        },
        "texto_completo": "texto completo...",
    }
    path = tmp_path / "T-999-23.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


class TestChunkSentencia:
    def _chunk(self, path):
        from data.scripts.chunk_documents import chunk_sentencia
        return chunk_sentencia(path)

    def test_returns_list_of_dicts(self, sample_sentencia):
        chunks = self._chunk(sample_sentencia)
        assert isinstance(chunks, list)
        assert all(isinstance(c, dict) for c in chunks)

    def test_chunk_has_required_fields(self, sample_sentencia):
        chunks = self._chunk(sample_sentencia)
        required = {"chunk_id", "text", "source_type", "sentencia_id", "tipo", "year", "tema", "seccion", "source_url"}
        for c in chunks:
            missing = required - c.keys()
            assert not missing, f"Chunk {c.get('chunk_id')} le faltan campos: {missing}"

    def test_source_type_is_sentencia(self, sample_sentencia):
        chunks = self._chunk(sample_sentencia)
        for c in chunks:
            assert c["source_type"] == "sentencia"

    def test_skips_empty_sections(self, sample_sentencia):
        chunks = self._chunk(sample_sentencia)
        secciones = {c["seccion"] for c in chunks}
        assert "resuelve" not in secciones

    def test_chunk_id_format(self, sample_sentencia):
        chunks = self._chunk(sample_sentencia)
        pattern = re.compile(r"^sentencia_[\w-]+_\w+_\d+$")
        for c in chunks:
            assert pattern.match(c["chunk_id"]), f"chunk_id inválido: {c['chunk_id']}"

    def test_preserves_metadata(self, sample_sentencia):
        chunks = self._chunk(sample_sentencia)
        for c in chunks:
            assert c["sentencia_id"] == "T-999-23"
            assert c["tipo"] == "T"
            assert c["year"] == 2023
            assert c["tema"] == "Derecho a la salud"


# ---------------------------------------------------------------------------
# build_output
# ---------------------------------------------------------------------------


class TestBuildOutput:
    def _build(self, const_chunks, sent_chunks):
        from data.scripts.chunk_documents import build_output
        return build_output(const_chunks, sent_chunks)

    def test_has_metadata_and_chunks(self):
        output = self._build(
            [{"chunk_id": "c1", "source_type": "constitucion"}],
            [{"chunk_id": "s1", "source_type": "sentencia"}],
        )
        assert "metadata" in output
        assert "chunks" in output

    def test_total_chunks_correct(self):
        const = [{"chunk_id": f"c{i}", "source_type": "constitucion"} for i in range(3)]
        sent = [{"chunk_id": f"s{i}", "source_type": "sentencia"} for i in range(5)]
        output = self._build(const, sent)
        assert output["metadata"]["total_chunks"] == 8
        assert len(output["chunks"]) == 8

    def test_source_counts_correct(self):
        const = [{"chunk_id": f"c{i}", "source_type": "constitucion"} for i in range(3)]
        sent = [{"chunk_id": f"s{i}", "source_type": "sentencia"} for i in range(5)]
        output = self._build(const, sent)
        assert output["metadata"]["sources"]["constitucion"] == 3
        assert output["metadata"]["sources"]["sentencias"] == 5
