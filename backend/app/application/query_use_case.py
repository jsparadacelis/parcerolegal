"""Use case: answer a legal question using RAG."""

from __future__ import annotations

import time

from backend.app.domain.entities import QueryResult, RetrievedChunk, Source
from backend.app.domain.ports import Embedder, LLMClient, VectorStore
from backend.app.domain.services import extract_sentencia_id, filter_by_score, is_out_of_scope

_OUT_OF_SCOPE_ANSWER = (
    "Tu pregunta está fuera del alcance de la legislación colombiana disponible. "
    "Por favor formula una pregunta relacionada con la Constitución Política de Colombia "
    "o las sentencias de la Corte Constitucional."
)

_SYSTEM_ROLE = """\
Eres un asistente jurídico especializado en derecho constitucional colombiano.
Responde ÚNICAMENTE basándote en los fragmentos de legislación proporcionados.

Reglas:
- Cita los fragmentos en tu respuesta usando [1], [2], etc.
- Si el contexto no cubre la pregunta, di: "Esta información no está disponible en los documentos proporcionados."
- No añadas información externa ni interpretaciones propias.
- Responde en español, con tono formal pero accesible para no especialistas.
- Usa párrafos cortos. Usa listas cuando mejoren la claridad.\
"""

_USER_TEMPLATE = """\
Fragmentos relevantes:
{context}

Pregunta: {question}\
"""


class QueryUseCase:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        llm: LLMClient,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._llm = llm

    def execute(self, question: str) -> QueryResult:
        start = time.time()

        embedding = self._embedder.embed(question)
        sentencia_id = extract_sentencia_id(question)
        chunks = self._store.search(embedding, top_k=5, sentencia_id=sentencia_id)
        filtered = chunks if sentencia_id and chunks else filter_by_score(chunks)

        elapsed_ms = lambda: (time.time() - start) * 1000

        if is_out_of_scope(filtered):
            return QueryResult(
                answer=_OUT_OF_SCOPE_ANSWER,
                sources=[],
                out_of_scope=True,
                processing_time_ms=elapsed_ms(),
            )

        context = "\n\n".join(
            f"[{i + 1}] {chunk.text}" for i, chunk in enumerate(filtered)
        )
        prompt = _USER_TEMPLATE.format(context=context, question=question)
        answer = self._llm.generate(prompt, system=_SYSTEM_ROLE)
        sources = [_chunk_to_source(chunk) for chunk in filtered]

        return QueryResult(
            answer=answer,
            sources=sources,
            out_of_scope=False,
            processing_time_ms=elapsed_ms(),
        )


def _chunk_to_source(chunk: RetrievedChunk) -> Source:
    if chunk.source_type == "constitucion":
        article_numero = chunk.metadata.get("article_numero", "")
        titulo = chunk.metadata.get("titulo", "")
        title = f"Art. {article_numero} — {titulo}" if article_numero else titulo
        url = chunk.metadata.get("url_original", "")
    else:
        title = chunk.metadata.get("sentencia_id", "")
        url = chunk.metadata.get("source_url", "")

    return Source(
        chunk_id=chunk.chunk_id,
        source_type=chunk.source_type,
        title=title,
        url=url,
    )
