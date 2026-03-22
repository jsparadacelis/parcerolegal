"""Tests for QueryUseCase — stub phase."""

import pytest

from backend.app.application.query_use_case import QueryUseCase
from backend.tests.conftest import FakeEmbedder, FakeLLMClient, FakeVectorStore


class TestQueryUseCase:
    def test_execute_raises_not_implemented(self):
        use_case = QueryUseCase(
            embedder=FakeEmbedder(),
            store=FakeVectorStore(),
            llm=FakeLLMClient(),
        )
        with pytest.raises(NotImplementedError, match="RAG pipeline"):
            use_case.execute("¿Qué dice el artículo 13?")

    def test_construction_with_ports(self):
        use_case = QueryUseCase(
            embedder=FakeEmbedder(),
            store=FakeVectorStore(),
            llm=FakeLLMClient(),
        )
        assert use_case._embedder is not None
        assert use_case._store is not None
        assert use_case._llm is not None
