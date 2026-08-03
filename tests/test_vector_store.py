"""tests/test_vector_store.py

Unit tests for app.ai.vector_store.VectorStore.

Tests are deliberately self-contained and fast:
- No network calls, no GitHub API, no model loading.
- Each test gets its own temporary JSON file via tmp_path (pytest built-in).
- Pure-Python cosine similarity is verified against known hand-calculated values.

Run with:
    .venv/Scripts/python -m pytest tests/ -v
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from app.ai.vector_store import VectorStore, SimilarityResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unit(n: int, pos: int) -> list[float]:
    """Return an n-dimensional unit vector with 1.0 at *pos* and 0.0 elsewhere."""
    v = [0.0] * n
    v[pos] = 1.0
    return v


def _make_store(tmp_path: Path) -> VectorStore:
    return VectorStore(tmp_path / "embeddings.json")


# ---------------------------------------------------------------------------
# Save & load
# ---------------------------------------------------------------------------

class TestSaveAndLoad:
    def test_save_creates_file(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save("alice", [1.0, 0.0, 0.0])
        assert (tmp_path / "embeddings.json").exists()

    def test_saved_vector_is_retrievable(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        vec = [0.5, 0.3, 0.2]
        store.save("bob", vec)
        assert store.get("bob") == vec

    def test_missing_username_returns_none(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.get("nobody") is None

    def test_overwrite_updates_vector(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save("alice", [1.0, 0.0])
        store.save("alice", [0.0, 1.0])
        assert store.get("alice") == [0.0, 1.0]

    def test_count_reflects_unique_usernames(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save("alice", [1.0, 0.0])
        store.save("bob", [0.0, 1.0])
        store.save("alice", [0.5, 0.5])  # overwrite
        assert store.count == 2

    def test_load_all_returns_snapshot(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save("alice", [1.0, 0.0])
        store.save("bob", [0.0, 1.0])
        snapshot = store.load_all()
        assert set(snapshot.keys()) == {"alice", "bob"}

    def test_persistence_across_instances(self, tmp_path: Path) -> None:
        """Data written by one VectorStore instance must be readable by a new one."""
        path = tmp_path / "embeddings.json"
        store1 = VectorStore(path)
        store1.save("alice", [1.0, 0.0, 0.0])

        store2 = VectorStore(path)
        assert store2.get("alice") == [1.0, 0.0, 0.0]

    def test_corrupted_file_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "embeddings.json"
        path.write_text("NOT VALID JSON", encoding="utf-8")
        store = VectorStore(path)
        assert store.count == 0

    def test_atomic_write_uses_tmp_file(self, tmp_path: Path) -> None:
        """Verify that the tmp file is cleaned up (i.e. renamed) after save."""
        store = _make_store(tmp_path)
        store.save("alice", [1.0])
        tmp_file = tmp_path / "embeddings.json.tmp"
        assert not tmp_file.exists(), "Temp file should be renamed after write"


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    """Test VectorStore._cosine_similarity via the private method directly."""

    def test_identical_vectors_score_one(self) -> None:
        v = [0.5, 0.3, 0.2]
        score = VectorStore._cosine_similarity(v, v)
        assert math.isclose(score, 1.0, rel_tol=1e-9)

    def test_orthogonal_vectors_score_zero(self) -> None:
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        assert math.isclose(VectorStore._cosine_similarity(a, b), 0.0, abs_tol=1e-9)

    def test_opposite_vectors_score_minus_one(self) -> None:
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert math.isclose(VectorStore._cosine_similarity(a, b), -1.0, rel_tol=1e-9)

    def test_zero_vector_returns_zero(self) -> None:
        a = [0.0, 0.0, 0.0]
        b = [1.0, 2.0, 3.0]
        assert VectorStore._cosine_similarity(a, b) == 0.0

    def test_known_value(self) -> None:
        # [1,1] vs [1,0]: cos = 1/sqrt(2) ≈ 0.7071
        a = [1.0, 1.0]
        b = [1.0, 0.0]
        expected = 1.0 / math.sqrt(2.0)
        assert math.isclose(VectorStore._cosine_similarity(a, b), expected, rel_tol=1e-6)

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="Vector length mismatch"):
            VectorStore._cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0])


# ---------------------------------------------------------------------------
# find_similar
# ---------------------------------------------------------------------------

class TestFindSimilar:
    def test_raises_key_error_for_unknown_username(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save("alice", [1.0, 0.0])
        with pytest.raises(KeyError):
            store.find_similar("ghost")

    def test_query_user_excluded_from_results(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save("alice", [1.0, 0.0])
        store.save("bob", [0.9, 0.1])
        results = store.find_similar("alice")
        usernames = [r.username for r in results]
        assert "alice" not in usernames

    def test_results_ordered_by_descending_similarity(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        # alice  = [1, 0, 0]  (query)
        # bob    = [1, 0, 0]  → similarity 1.0  (most similar)
        # carol  = [0, 1, 0]  → similarity 0.0
        # dave   = [1, 1, 0]  → similarity ~0.707
        store.save("alice", _unit(3, 0))
        store.save("bob",   _unit(3, 0))
        store.save("carol", _unit(3, 1))
        store.save("dave",  [1.0, 1.0, 0.0])

        results = store.find_similar("alice")
        scores = [r.similarity for r in results]
        assert scores == sorted(scores, reverse=True), "Results must be ordered descending"
        assert results[0].username == "bob"

    def test_top_n_limits_results(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save("query", [1.0, 0.0])
        for i in range(10):
            store.save(f"user{i}", [float(i % 3), float(i % 5)])

        results = store.find_similar("query", top_n=3)
        assert len(results) <= 3

    def test_single_other_user_returns_one_result(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save("alice", [1.0, 0.0])
        store.save("bob", [0.0, 1.0])
        results = store.find_similar("alice")
        assert len(results) == 1
        assert results[0].username == "bob"

    def test_returns_similarity_result_objects(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save("alice", [1.0, 0.0])
        store.save("bob", [1.0, 0.0])
        results = store.find_similar("alice")
        assert all(isinstance(r, SimilarityResult) for r in results)

    def test_similarity_is_rounded_to_six_decimal_places(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save("alice", [1.0, 1.0])
        store.save("bob", [1.0, 0.0])
        results = store.find_similar("alice")
        # The exact value should be 1/sqrt(2); check it's rounded to 6dp
        assert results[0].similarity == round(results[0].similarity, 6)
