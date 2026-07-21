from __future__ import annotations
from typing import TypedDict, Any, Optional


class PipelineState(TypedDict, total=False):
    # --- input ---
    username: str
    code_snippet: str

    # --- github_node output ---
    github_raw_data: dict[str, Any]
    github_status: str

    # --- embedding_node output ---
    embedding_vector: list[float]
    embedding_vector_shape: list[int]
    embedding_status: str

    # --- scoring_node output ---
    pytorch_developer_score: float
    scoring_status: str

    starcoder_quality_metrics: dict[str, Any]
    starcoder_status: str

    vector_similarity_results: dict[str, str]
    similarity_status: str