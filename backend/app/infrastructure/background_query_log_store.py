"""Wrapper no-bloqueante para QueryLogStore.

Compone el fire-and-forget encima de cualquier QueryLogStore: `save` delega
al store envuelto en un thread-pool y retorna al instante, sin bloquear la
respuesta al usuario. Los errores del guardado los traga el store envuelto; aquí
además blindamos el `submit` para que un executor apagado tampoco propague.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from backend.app.domain.entities import QueryLog
from backend.app.domain.ports import QueryLogStore

logger = logging.getLogger("parcerolegal")


class BackgroundQueryLogStore:
    def __init__(
        self,
        inner: QueryLogStore,
        executor: ThreadPoolExecutor | None = None,
    ) -> None:
        self._inner = inner
        self._executor = executor or ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="query-log"
        )

    def save(self, log: QueryLog) -> None:
        try:
            self._executor.submit(self._inner.save, log)
        except RuntimeError:  # executor apagado — best-effort, no debe propagar
            logger.warning("no se pudo encolar el log de la consulta", exc_info=True)
