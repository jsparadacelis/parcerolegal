"""Wrapper no-bloqueante para MissedQueryStore.

Compone el fire-and-forget encima de cualquier MissedQueryStore: `save` delega
al store envuelto en un thread-pool y retorna al instante, sin bloquear la
respuesta al usuario. Los errores del guardado los traga el store envuelto; aquí
además blindamos el `submit` para que un executor apagado tampoco propague.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from backend.app.domain.entities import MissedQuery
from backend.app.domain.ports import MissedQueryStore

logger = logging.getLogger("parcerolegal")


class BackgroundMissedQueryStore:
    def __init__(
        self,
        inner: MissedQueryStore,
        executor: ThreadPoolExecutor | None = None,
    ) -> None:
        self._inner = inner
        self._executor = executor or ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="missed-query"
        )

    def save(self, missed: MissedQuery) -> None:
        try:
            self._executor.submit(self._inner.save, missed)
        except RuntimeError:  # executor apagado — best-effort, no debe propagar
            logger.warning("no se pudo encolar la pregunta fuera de alcance", exc_info=True)
