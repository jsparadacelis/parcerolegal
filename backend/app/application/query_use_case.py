"""Use case: answer a legal question using RAG."""

from __future__ import annotations

import logging
import time

from backend.app.domain.entities import (
    SOURCE_TYPE_CODIGO_PENAL,
    SOURCE_TYPE_CODIGO_SUSTANTIVO_TRABAJO,
    SOURCE_TYPE_CONSTITUCION,
    QueryLog,
    QueryResult,
    RetrievedChunk,
    Source,
)
from backend.app.domain.ports import (
    Embedder,
    LLMClient,
    QueryLogStore,
    VectorStore,
)
from backend.app.domain.services import (
    dedupe_sources,
    detect_legal_area,
    extract_sentencia_id,
    filter_by_score,
    is_out_of_scope,
    is_single_document_answer,
    sanitize_citations,
)

logger = logging.getLogger("parcerolegal")

_SCOPE = (
    "la Constitución Política de Colombia, las sentencias de la Corte "
    "Constitucional, el Código Penal (delitos y sus penas) y el Código "
    "Sustantivo del Trabajo (contrato de trabajo, despido y derecho colectivo)"
)


def _build_out_of_scope_answer(question: str) -> str:
    """Mensaje de fuera-de-alcance: reconoce el tema cuando se puede y orienta."""
    area = detect_legal_area(question)
    if area:
        return (
            f"Tu pregunta parece tratar sobre {area}, un tema que todavía no está en "
            f"el corpus de Parcero Legal. Por ahora solo respondemos con base en "
            f"{_SCOPE}. Para este caso te recomendamos revisar la normativa "
            "correspondiente o consultar a un abogado."
        )
    return (
        "No encontré información sobre tu pregunta en el corpus de Parcero Legal, que "
        f"hoy cubre {_SCOPE}. Intenta reformularla en términos de derechos "
        "constitucionales, o consulta a un abogado para tu caso puntual."
    )

_SYSTEM_ROLE_TEMPLATE = """\
Eres un asistente jurídico especializado en derecho constitucional, penal y laboral colombiano.
Responde ÚNICAMENTE basándote en los fragmentos de legislación proporcionados.

Reglas:
- Tienes exactamente {n} fragmentos, numerados [1] a [{n}].
- Cita los fragmentos en tu respuesta usando [1], [2], etc.
- Nunca cites un número de fragmento mayor que {n} ni menor que 1: está prohibido inventar citas.
- Si los fragmentos entregados provienen de un único caso judicial con circunstancias específicas (p. ej., un grupo protegido o una situación particular), acláralo en tu respuesta y no la presentes como una regla general aplicable a todos los casos.
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
        top_k: int,
        query_log_store: QueryLogStore | None = None,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._llm = llm
        self._top_k = top_k
        self._query_log_store = query_log_store

    def execute(self, question: str) -> QueryResult:
        start = time.time()

        embedding = self._embedder.embed(question)
        sentencia_id = extract_sentencia_id(question)
        chunks = self._store.search(embedding, top_k=self._top_k, sentencia_id=sentencia_id)
        filtered = chunks if sentencia_id and chunks else filter_by_score(chunks)

        elapsed_ms = lambda: (time.time() - start) * 1000

        if is_out_of_scope(filtered):
            answer = _build_out_of_scope_answer(question)
            self._record_query(question, answer, chunks, sources=[], out_of_scope=True)
            return QueryResult(
                answer=answer,
                sources=[],
                out_of_scope=True,
                processing_time_ms=elapsed_ms(),
            )

        context = "\n\n".join(
            f"[{i + 1}] {chunk.text}" for i, chunk in enumerate(filtered)
        )
        prompt = _USER_TEMPLATE.format(context=context, question=question)
        system_role = _SYSTEM_ROLE_TEMPLATE.format(n=len(filtered))
        answer = self._llm.generate(prompt, system=system_role)
        answer, invalid_citations = sanitize_citations(answer, valid_count=len(filtered))
        if invalid_citations:
            logger.warning(
                "citas alucinadas detectadas y removidas: %s (fragmentos_disponibles=%d)",
                invalid_citations,
                len(filtered),
            )
        raw_sources = [_chunk_to_source(chunk) for chunk in filtered]
        sources = dedupe_sources(raw_sources)

        if sentencia_id is None:
            area = detect_legal_area(question)
            if area and is_single_document_answer(raw_sources):
                answer = _append_narrow_source_caveat(answer, area, sources[0].title)

        self._record_query(question, answer, chunks, sources=sources, out_of_scope=False)

        return QueryResult(
            answer=answer,
            sources=sources,
            out_of_scope=False,
            processing_time_ms=elapsed_ms(),
        )

    def _record_query(
        self,
        question: str,
        answer: str,
        chunks: list[RetrievedChunk],
        sources: list[Source],
        out_of_scope: bool,
    ) -> None:
        """Persiste la consulta respondida, best-effort.

        Fire-and-forget: cualquier fallo se loguea pero jamás rompe la respuesta.
        """
        if self._query_log_store is None:
            return
        record = QueryLog(
            question=question,
            answer=answer,
            sources=sources,
            top_score=chunks[0].score if chunks else None,
            detected_area=detect_legal_area(question),
            out_of_scope=out_of_scope,
        )
        try:
            self._query_log_store.save(record)
        except Exception:  # noqa: BLE001 — best-effort, no debe afectar la consulta
            logger.exception("no se pudo guardar la consulta")


def _append_narrow_source_caveat(answer: str, area: str, document_title: str) -> str:
    """Advierte cuando toda la respuesta descansa en un único documento (p.ej.
    una sentencia sobre un caso puntual) para una pregunta de un área que el
    corpus no cubre en general (ver `_LEGAL_AREAS`)."""
    return (
        f"{answer}\n\n"
        f"**Nota:** esta respuesta se basa únicamente en {document_title}, un caso "
        f"judicial puntual, no en la norma general de {area}. Si tu situación no "
        "coincide exactamente con ese caso, te recomendamos revisar la normativa "
        "correspondiente o consultar a un abogado."
    )


def _chunk_to_source(chunk: RetrievedChunk) -> Source:
    if chunk.source_type == SOURCE_TYPE_CONSTITUCION:
        article_numero = chunk.metadata.get("article_numero", "")
        titulo = chunk.metadata.get("titulo", "")
        title = f"Art. {article_numero} — {titulo}" if article_numero else titulo
        url = chunk.metadata.get("url_original", "")
    elif chunk.source_type == SOURCE_TYPE_CODIGO_PENAL:
        title = _codigo_penal_title(chunk.metadata)
        url = chunk.metadata.get("url_original", "")
    elif chunk.source_type == SOURCE_TYPE_CODIGO_SUSTANTIVO_TRABAJO:
        title = _cst_title(chunk.metadata)
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


def _codigo_penal_title(metadata: dict) -> str:
    """'Art. 239 CP — Hurto' — o solo 'Art. 447A CP' si 'nombre' quedó vacío en
    el scraper (~50/480 artículos, ver .aiplans/scrape-codigo-penal): sin <em>
    ni nombre reconocible en el <strong> de encabezado."""
    article_numero = metadata.get("article_numero", "")
    sufijo = metadata.get("sufijo") or ""
    nombre = metadata.get("nombre") or ""
    numero_label = f"{article_numero}{sufijo}"
    if not numero_label:
        return nombre
    if nombre:
        return f"Art. {numero_label} CP — {nombre}"
    return f"Art. {numero_label} CP"


def _cst_title(metadata: dict) -> str:
    """'Art. 64 CST — Terminación Unilateral...' — o solo 'Art. 391-1 CST' si
    'nombre' quedó vacío en el scraper (ver
    .aiplans/ingest-codigo-sustantivo-trabajo), mismo criterio de degradación
    que _codigo_penal_title."""
    article_numero = metadata.get("article_numero", "")
    sufijo = metadata.get("sufijo") or ""
    nombre = metadata.get("nombre") or ""
    numero_label = f"{article_numero}-{sufijo}" if sufijo else f"{article_numero}"
    if not numero_label:
        return nombre
    if nombre:
        return f"Art. {numero_label} CST — {nombre}"
    return f"Art. {numero_label} CST"
