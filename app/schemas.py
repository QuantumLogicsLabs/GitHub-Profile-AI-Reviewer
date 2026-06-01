from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    username: str = Field(min_length=1, max_length=39, pattern=r"^[A-Za-z0-9-]+$")


class GraphQLSignals(BaseModel):
    total_commits: int
    merged_prs: int
    total_contributions: int


class StreakData(BaseModel):
    current_streak: int
    longest_streak: int


class AnalyzeResponse(BaseModel):
    username: str
    developer_level: str
    confidence: float
    strongest_language: str
    language_breakdown: dict[str, int]
    hiring_readiness_score: int
    consistency_score: int
    graphql_signals: GraphQLSignals
    streak_data: StreakData
    model_info: dict[str, Any]
