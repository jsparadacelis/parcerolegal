"""Tests for BackgroundQueryLogStore — wrapper no-bloqueante.

Verifica el fire-and-forget de verdad: `save` delega al store envuelto en un
thread-pool y retorna al instante, sin bloquear la respuesta.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import create_autospec

import pytest

from backend.app.domain.entities import QueryLog
from backend.app.domain.ports import QueryLogStore
from backend.app.infrastructure.background_query_log_store import (
    BackgroundQueryLogStore,
)


def a_query_log() -> QueryLog:
    return QueryLog(
        question="¿Cuánto cuesta el arroz?",
        answer="fuera de alcance...",
        sources=[],
        top_score=0.30,
        detected_area=None,
        out_of_scope=True,
    )


@pytest.fixture
def inner() -> QueryLogStore:
    return create_autospec(QueryLogStore, spec_set=True, instance=True)


class TestBackgroundQueryLogStore:
    def test_delegates_save_to_inner_store(self, inner):
        executor = ThreadPoolExecutor(max_workers=1)
        store = BackgroundQueryLogStore(inner, executor=executor)

        store.save(a_query_log())
        executor.shutdown(wait=True)

        inner.save.assert_called_once_with(a_query_log())

    def test_save_does_not_block_on_slow_inner(self, inner):
        started = threading.Event()
        release = threading.Event()

        def slow_save(log: QueryLog) -> None:
            started.set()
            release.wait(timeout=1)

        inner.save.side_effect = slow_save
        store = BackgroundQueryLogStore(inner, executor=ThreadPoolExecutor(max_workers=1))

        store.save(a_query_log())  # si bloqueara, colgaría en release.wait

        assert started.wait(timeout=1)  # el inner arrancó en otro hilo
        release.set()

    def test_swallows_when_executor_already_shutdown(self, inner):
        executor = ThreadPoolExecutor(max_workers=1)
        executor.shutdown(wait=True)
        store = BackgroundQueryLogStore(inner, executor=executor)

        store.save(a_query_log())  # best-effort: submit rechazado no debe propagar
