"""Use case: busca una consulta ya respondida por su share_token.

No vuelve a llamar al pipeline RAG — el share_token identifica un registro
que QueryUseCase ya generó y persistió en el log de consultas (ver
domain.entities.QueryLog). Compartir es instantáneo porque no hay nada que
recalcular: la respuesta ya existe desde el momento en que se contestó la
pregunta original.
"""

from __future__ import annotations

from backend.app.domain.entities import QueryLog
from backend.app.domain.ports import QueryLogFinder


class GetSharedQueryUseCase:
    def __init__(self, finder: QueryLogFinder) -> None:
        self._finder = finder

    def execute(self, share_token: str) -> QueryLog | None:
        return self._finder.find_by_share_token(share_token)
