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


class PublicActivity(BaseModel):
    public_commits: int
    public_prs_created: int


class AnalyzeResponse(BaseModel):
    username: str
    rating_score: int = Field(ge=0, le=100)
    developer_level: str
    confidence: float
    strongest_language: str
    language_breakdown: dict[str, int]
    hiring_readiness_score: int = Field(ge=0, le=100)
    consistency_score: int = Field(ge=0, le=100)
    public_activity: PublicActivity
    graphql_signals: GraphQLSignals
    streak_data: StreakData
    model_info: dict[str, Any]


class OrgAnalyzeRequest(BaseModel):
    org: str = Field(min_length=1, max_length=39, pattern=r"^[A-Za-z0-9-]+$")
    max_members: int | None = Field(default=None, ge=1, le=500)


class OrgMemberError(BaseModel):
    username: str
    error: str


class OrgAnalyzeResponse(BaseModel):
    org: str
    total_members: int
    analyzed_count: int
    failed_count: int
    ranked_results: list[AnalyzeResponse]
    failures: list[OrgMemberError]