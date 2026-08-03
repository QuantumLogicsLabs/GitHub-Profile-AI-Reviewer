"""app/ai/vector_store.py

Persists username→embedding-vector mappings to a JSON file and provides
cosine-similarity search over the stored vectors.

Design notes:
- Storage: a single JSON file (`data/embeddings.json` by default, configurable
  via the `EMBEDDING_STORE_PATH` env-var / settings field).  This matches the
  codebase's current scale — no extra dependencies required.
- Similarity: pure-Python cosine similarity using `math`.  `torch` and `numpy`
  are deliberately not used here to keep this utility lean; the hot path is
  the embedding model call in CodeEmbeddingService, not this search step.
- Thread-safety: a `threading.Lock` guards every file write so concurrent
  FastAPI requests don't corrupt the JSON file.
- Module-level singleton `vector_store` mirrors the `settings` pattern in
  `app/core/config.py`.
"""
from __future__ import annotations

import json
import math
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.config import settings


@dataclass
class SimilarityResult:
    """A single result from a similarity search."""

    username: str
    similarity: float


class VectorStore:
    """Persist and search developer embedding vectors.

    Attributes:
        _path: Absolute path to the backing JSON file.
        _lock: Threading lock that serialises all write operations.
        _cache: In-memory copy of the on-disk store, kept in sync on every
                save so reads never need to re-parse the file.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        self._cache: dict[str, list[float]] = self._load_from_disk()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_from_disk(self) -> dict[str, list[float]]:
        """Read the JSON file from disk.  Returns an empty dict on first run."""
        if not self._path.exists():
            return {}
        try:
            with self._path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return {k: v for k, v in data.items() if isinstance(v, list)}
        except (json.JSONDecodeError, OSError):
            return {}
        return {}

    def _flush_to_disk(self) -> None:
        """Write the current in-memory cache to disk (caller holds _lock)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(self._cache, fh)
        tmp.replace(self._path)  # atomic on most OSes

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Return the cosine similarity between two equal-length vectors.

        Returns 0.0 if either vector is the zero vector.
        """
        if len(a) != len(b):
            raise ValueError(
                f"Vector length mismatch: {len(a)} vs {len(b)}"
            )
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(y * y for y in b))
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot / (mag_a * mag_b)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, username: str, vector: list[float]) -> None:
        """Persist *username*'s embedding vector.

        Overwrites any previously stored vector for the same username, so
        re-analyzing a profile refreshes its embedding automatically.

        Args:
            username: GitHub username (case-sensitive).
            vector: Flat list of floats produced by CodeEmbeddingService.
        """
        with self._lock:
            self._cache[username] = vector
            self._flush_to_disk()

    def get(self, username: str) -> Optional[list[float]]:
        """Return the stored vector for *username*, or ``None`` if absent."""
        return self._cache.get(username)

    def load_all(self) -> dict[str, list[float]]:
        """Return a snapshot of all stored username→vector mappings."""
        return dict(self._cache)

    @property
    def count(self) -> int:
        """Number of profiles currently indexed."""
        return len(self._cache)

    def find_similar(
        self,
        username: str,
        top_n: int = 10,
    ) -> list[SimilarityResult]:
        """Find the *top_n* developers most similar to *username*.

        Args:
            username: GitHub username whose vector to use as the query.
            top_n: Maximum number of results to return.

        Returns:
            List of :class:`SimilarityResult` ordered by descending similarity.
            The query username itself is excluded from the results.

        Raises:
            KeyError: If *username* has no stored vector.
        """
        query_vector = self._cache.get(username)
        if query_vector is None:
            raise KeyError(username)

        scores: list[SimilarityResult] = []
        for other_username, other_vector in self._cache.items():
            if other_username == username:
                continue
            sim = self._cosine_similarity(query_vector, other_vector)
            scores.append(SimilarityResult(username=other_username, similarity=round(sim, 6)))

        scores.sort(key=lambda r: r.similarity, reverse=True)
        return scores[:top_n]


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere instead of constructing a
# new instance, so the in-memory cache is shared across the whole process.
# ---------------------------------------------------------------------------
vector_store = VectorStore(settings.embedding_store_path)
