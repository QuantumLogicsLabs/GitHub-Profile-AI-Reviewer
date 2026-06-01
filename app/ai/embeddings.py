from __future__ import annotations

from typing import Iterable

from app.core.config import settings

try:
    import torch
    from transformers import AutoModel, AutoTokenizer
except Exception:
    torch = None
    AutoModel = None
    AutoTokenizer = None


class CodeEmbeddingService:
    def __init__(self) -> None:
        self._dim = settings.embedding_dim
        self._ready = False
        self._tokenizer = None
        self._model = None

        if AutoModel is not None and AutoTokenizer is not None:
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(settings.codebert_model)
                self._model = AutoModel.from_pretrained(settings.codebert_model)
                self._model.eval()
                self._ready = True
            except Exception:
                self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def embedding_dim(self) -> int:
        return self._dim

    def embed_repository_signals(self, snippets: Iterable[str]) -> list[float]:
        text = "\n".join(snippets).strip()
        if not text:
            return [0.0] * self._dim

        if self._ready and torch is not None and self._tokenizer is not None and self._model is not None:
            tokens = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self._model(**tokens)
            cls = outputs.last_hidden_state[:, 0, :].squeeze(0)
            return cls.tolist()

        vector = [0.0] * self._dim
        for i, ch in enumerate(text):
            vector[i % self._dim] += (ord(ch) % 31) / 31.0
        norm = sum(abs(v) for v in vector) or 1.0
        return [v / norm for v in vector]
