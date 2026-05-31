"""HuggingFace Inference API embedder — no local model, no PyTorch/ONNX required."""

from __future__ import annotations

import requests


class SentenceTransformerEmbedder:
    _BASE = "https://router.huggingface.co/hf-inference/pipeline/feature-extraction"

    def __init__(self, model_name: str, hf_token: str = "") -> None:
        self._url = f"{self._BASE}/{model_name}"
        self._headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}

    def embed(self, text: str) -> list[float]:
        response = requests.post(
            self._url,
            json={"inputs": text},
            headers=self._headers,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        if data and isinstance(data[0], list):
            return data[0]
        return data
