from __future__ import annotations

from collections import defaultdict
import math
from typing import Any

from app.ai.embeddings import CodeEmbeddingService
from app.ai.scoring import ScoringEngine
from app.ai.vector_store import vector_store
from app.clients.github_graphql import GitHubGraphQLClient
from app.core.config import settings
from app.clients.streak import compute_streak_from_calendar
from app.graph.state import ProfileState


def _extract_features(user: dict[str, Any]) -> tuple[dict[str, int], dict[str, int], list[str]]:
    repositories = user.get("repositories", {}).get("nodes", [])
    language_sizes: dict[str, int] = defaultdict(int)
    repo_snippets: list[str] = []
    total_commits = 0
    total_stars = 0
    total_forks = 0

    for repo in repositories:
        name = repo.get("name") or ""
        desc = repo.get("description") or ""
        primary = (repo.get("primaryLanguage") or {}).get("name") or ""
        repo_snippets.append(f"repo:{name} lang:{primary} desc:{desc}")
        total_stars += int(repo.get("stargazerCount", 0))
        total_forks += int(repo.get("forkCount", 0))

        default_branch = repo.get("defaultBranchRef") or {}
        history = (default_branch.get("target") or {}).get("history", {})
        total_commits += int(history.get("totalCount", 0))

        for edge in repo.get("languages", {}).get("edges", []):
            lang_name = edge.get("node", {}).get("name") or "Unknown"
            language_sizes[lang_name] += int(edge.get("size", 0))

    merged_prs = int(user.get("pullRequests", {}).get("totalCount", 0))
    contributions = user.get("contributionsCollection", {})
    public_activity = user.get("publicActivity", {})
    public_commits = int(public_activity.get("publicCommits", contributions.get("totalCommitContributions", 0)) or 0)
    public_prs_created = int(public_activity.get("publicPRsCreated", contributions.get("totalPullRequestContributions", 0)) or 0)
    total_contributions = int(contributions.get("contributionCalendar", {}).get("totalContributions", 0))
    followers = int(user.get("followers", {}).get("totalCount", 0))
    metrics = {
        "repo_count": len(repositories),
        "total_commits": total_commits,
        "merged_prs": merged_prs,
        "public_commits": public_commits,
        "public_prs_created": public_prs_created,
        "total_contributions": total_contributions,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "followers": followers,
    }
    return dict(language_sizes), metrics, repo_snippets


def _scale_log(value: int, weight: int, factor: float = 2.0) -> int:
    return min(weight, int(math.log1p(max(value, 0)) * factor))


def _normalize_activity(metrics: dict[str, int], data_source: str) -> int:
    contribution_divisor = 12 if data_source == "rest-public" else 25
    score = 0
    score += min(30, metrics["total_contributions"] // contribution_divisor)
    score += min(18, metrics["repo_count"] * 2)
    score += min(17, metrics["total_commits"] // 80)
    score += min(12, metrics["merged_prs"] // 3)
    score += _scale_log(metrics["total_stars"], 10, 2.2)
    score += _scale_log(metrics["total_forks"], 6, 2.0)
    score += _scale_log(metrics["followers"], 7, 1.8)
    return int(max(0, min(100, score)))


def _normalize_consistency(current_streak: int, longest_streak: int) -> int:
    if longest_streak <= 0:
        return 0
    active_now = min(35, current_streak * 5)
    proven_consistency = min(65, longest_streak * 3)
    return int(max(0, min(100, active_now + proven_consistency)))


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
        lang_sizes, metrics, snippets = _extract_features(user)
        strongest_language, breakdown = _language_breakdown(lang_sizes)

        weeks = user.get("contributionsCollection", {}).get("contributionCalendar", {}).get("weeks", [])
        streak = compute_streak_from_calendar(weeks)
        consistency_score = _normalize_consistency(streak.current_streak, streak.longest_streak)

        embedding = self._embedder.embed_repository_signals(snippets)

        # Persist the embedding so this profile is searchable via /similar/.
        # Uses the module-level singleton — no second model load.
        vector_store.save(username, embedding)

        activity_score = _normalize_activity(metrics, raw.get("source", "graphql"))
        scored = self._scorer.infer(embedding, activity_score, consistency_score)

        state["final_report"] = {
            "username": username,
            "rating_score": scored.hiring_score,
            "developer_level": scored.level,
            "confidence": scored.confidence,
            "strongest_language": strongest_language,
            "language_breakdown": breakdown,
            "hiring_readiness_score": scored.hiring_score,
            "consistency_score": consistency_score,
            "public_activity": {
                "public_commits": metrics["public_commits"],
                "public_prs_created": metrics["public_prs_created"],
            },
            "graphql_signals": {
                "total_commits": metrics["total_commits"],
                "merged_prs": metrics["merged_prs"],
                "total_contributions": metrics["total_contributions"],
            },
            "streak_data": {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
            },
            "model_info": {
                "embedding_model": "microsoft/codebert-base",
                "scoring_model": settings.scoring_backend,
                "embedding_dim": self._embedder.embedding_dim,
                "embedding_backend": "transformers" if self._embedder.ready else "deterministic-fallback",
                "data_source": raw.get("source", "graphql"),
                "public_metrics": {
                    "repositories": metrics["repo_count"],
                    "stars": metrics["total_stars"],
                    "forks": metrics["total_forks"],
                    "followers": metrics["followers"],
                },
            },
        }
        return state
