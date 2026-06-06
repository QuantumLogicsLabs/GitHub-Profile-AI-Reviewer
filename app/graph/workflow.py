from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.ai.embeddings import CodeEmbeddingService
from app.ai.scoring import ScoringEngine
from app.clients.github_graphql import GitHubGraphQLClient
from app.clients.streak import compute_streak_from_calendar
from app.graph.state import ProfileState


def _extract_features(user: dict[str, Any]) -> tuple[dict[str, int], int, int, int, list[str]]:
    repositories = user.get("repositories", {}).get("nodes", [])
    language_sizes: dict[str, int] = defaultdict(int)
    repo_snippets: list[str] = []
    total_commits = 0

    for repo in repositories:
        name = repo.get("name") or ""
        desc = repo.get("description") or ""
        primary = (repo.get("primaryLanguage") or {}).get("name") or ""
        repo_snippets.append(f"repo:{name} lang:{primary} desc:{desc}")

        default_branch = repo.get("defaultBranchRef") or {}
        history = (default_branch.get("target") or {}).get("history", {})
        total_commits += int(history.get("totalCount", 0))

        for edge in repo.get("languages", {}).get("edges", []):
            lang_name = edge.get("node", {}).get("name") or "Unknown"
            language_sizes[lang_name] += int(edge.get("size", 0))

    merged_prs = int(user.get("pullRequests", {}).get("totalCount", 0))
    total_contributions = int(user.get("contributionsCollection", {}).get("contributionCalendar", {}).get("totalContributions", 0))
    return dict(language_sizes), total_commits, merged_prs, total_contributions, repo_snippets


def _normalize_activity(total_contributions: int, total_commits: int, merged_prs: int) -> int:
    a = min(45, total_contributions // 20)
    b = min(30, total_commits // 40)
    c = min(25, merged_prs // 4)
    return int(max(0, min(100, a + b + c)))


def _language_breakdown(language_sizes: dict[str, int]) -> tuple[str, dict[str, int]]:
    if not language_sizes:
        return "Unknown", {}
    strongest = max(language_sizes.items(), key=lambda x: x[1])[0]
    total = sum(language_sizes.values()) or 1
    breakdown = {lang: int((size / total) * 100) for lang, size in sorted(language_sizes.items(), key=lambda x: x[1], reverse=True)}
    return strongest, breakdown


class AnalyzerWorkflow:
    def __init__(self) -> None:
        self._github = GitHubGraphQLClient()
        self._embedder = CodeEmbeddingService()
        self._scorer = ScoringEngine(input_dim=self._embedder.embedding_dim)

    async def run(self, username: str) -> ProfileState:
        state: ProfileState = {"username": username}
        raw = await self._github.analyze_user(username)
        state["graphql_data"] = raw

        user = raw["data"]["user"]
        lang_sizes, total_commits, merged_prs, total_contributions, snippets = _extract_features(user)
        strongest_language, breakdown = _language_breakdown(lang_sizes)

        weeks = user.get("contributionsCollection", {}).get("contributionCalendar", {}).get("weeks", [])
        streak = compute_streak_from_calendar(weeks)
        consistency_score = int((streak.current_streak / streak.longest_streak) * 100) if streak.longest_streak > 0 else 0

        embedding = self._embedder.embed_repository_signals(snippets)
        activity_score = _normalize_activity(total_contributions, total_commits, merged_prs)
        scored = self._scorer.infer(embedding, activity_score, consistency_score)

        state["final_report"] = {
            "username": username,
            "developer_level": scored.level,
            "confidence": scored.confidence,
            "strongest_language": strongest_language,
            "language_breakdown": breakdown,
            "hiring_readiness_score": scored.hiring_score,
            "consistency_score": consistency_score,
            "graphql_signals": {
                "total_commits": total_commits,
                "merged_prs": merged_prs,
                "total_contributions": total_contributions,
            },
            "streak_data": {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
            },
            "model_info": {
                "embedding_model": "microsoft/codebert-base",
                "scoring_model": "DeveloperScoringModel",
                "embedding_dim": self._embedder.embedding_dim,
                "embedding_backend": "transformers" if self._embedder.ready else "deterministic-fallback",
            },
        }
        return state
