"""Use case: publica una pregunta bajo un link compartible.

Vuelve a correr QueryUseCase.execute() en vez de confiar en una respuesta
enviada por el cliente — ver domain.entities.SharedAnswer para el porqué.
"""

from __future__ import annotations

import secrets

from backend.app.application.query_use_case import QueryUseCase
from backend.app.domain.entities import SharedAnswer
from backend.app.domain.ports import SharedAnswerStore
from backend.app.infrastructure.config import SHARE_ID_BYTES


class ShareAnswerUseCase:
    def __init__(self, query_use_case: QueryUseCase, store: SharedAnswerStore) -> None:
        self._query_use_case = query_use_case
        self._store = store

    def execute(self, question: str) -> str:
        result = self._query_use_case.execute(question)
        share_id = secrets.token_urlsafe(SHARE_ID_BYTES)
        self._store.save(
            SharedAnswer(
                id=share_id,
                question=question,
                answer=result.answer,
                sources=result.sources,
                out_of_scope=result.out_of_scope,
            )
        )
        return share_id
