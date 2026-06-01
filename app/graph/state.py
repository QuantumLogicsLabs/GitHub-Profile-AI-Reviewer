from __future__ import annotations

from typing import Any, TypedDict


class ProfileState(TypedDict, total=False):
    username: str
    graphql_data: dict[str, Any]
    language_embeddings: list[float]
    feature_vector: list[float]
    strongest_language: str
    language_breakdown: dict[str, int]
    total_commits: int
    merged_prs: int
    total_contributions: int
    consistency_score: int
    current_streak: int
    longest_streak: int
    developer_level: str
    confidence: float
    hiring_score: int
    final_report: dict[str, Any]
