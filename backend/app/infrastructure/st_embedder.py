"""fastembed adapter — implements Embedder port via ONNX (no PyTorch required)."""

from __future__ import annotations

from fastembed import TextEmbedding


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, text: str) -> list[float]:
        return next(iter(self._model.embed([text]))).tolist()
