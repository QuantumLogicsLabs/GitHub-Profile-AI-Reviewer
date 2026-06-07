from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.clients.queries import ANALYZE_PROFILE_QUERY
from app.core.config import settings


class GitHubAPIError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


def _extract_total_count(response: httpx.Response, fallback: int) -> int:
    link = response.headers.get("Link", "")
    for part in link.split(","):
        if 'rel="last"' not in part:
            continue
        marker = "page="
        if marker not in part:
            continue
        value = part.split(marker, 1)[1].split("&", 1)[0].split(">", 1)[0]
        try:
            return int(value)
        except ValueError:
            return fallback
    return fallback


class GitHubGraphQLClient:
    async def analyze_user(self, username: str) -> dict[str, Any]:
        if not settings.github_token:
            return await self._analyze_public_user(username)

        payload = {"query": ANALYZE_PROFILE_QUERY, "variables": {"username": username}}

        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(settings.github_api_url, headers=_headers(), json=payload)

        if response.status_code >= 400:
            raise GitHubAPIError(f"GitHub API status={response.status_code}: {response.text}")

        data = response.json()
        if data.get("errors"):
            raise GitHubAPIError(str(data["errors"]))
        if data.get("data", {}).get("user") is None:
            raise GitHubAPIError(f"GitHub user '{username}' not found.")

        data["source"] = "graphql"
        return data

    async def _analyze_public_user(self, username: str) -> dict[str, Any]:
        base_url = settings.github_rest_api_url.rstrip("/")
        async with httpx.AsyncClient(base_url=base_url, timeout=settings.request_timeout_seconds, headers=_headers()) as client:
            user_response = await client.get(f"/users/{username}")
            if user_response.status_code == 404:
                raise GitHubAPIError(f"GitHub user '{username}' not found.")
            if user_response.status_code >= 400:
                raise GitHubAPIError(f"GitHub API status={user_response.status_code}: {user_response.text}")

            repos_response = await client.get(
                f"/users/{username}/repos",
                params={
                    "per_page": min(max(settings.github_public_repo_limit, 1), 100),
                    "sort": "updated",
                    "direction": "desc",
                    "type": "owner",
                },
            )
            if repos_response.status_code >= 400:
                raise GitHubAPIError(f"GitHub API status={repos_response.status_code}: {repos_response.text}")

            events_response = await client.get(f"/users/{username}/events/public", params={"per_page": 100})
            events = events_response.json() if events_response.status_code < 400 else []

            user = user_response.json()
            repos = repos_response.json()
            repo_nodes = await self._build_public_repositories(client, username, repos)
            weeks = _weeks_from_events(events)

        return {
            "source": "rest-public",
            "data": {
                "user": {
                    "login": user.get("login", username),
                    "name": user.get("name"),
                    "bio": user.get("bio"),
                    "createdAt": user.get("created_at"),
                    "followers": {"totalCount": int(user.get("followers") or 0)},
                    "contributionsCollection": {
                        "totalCommitContributions": sum(_event_commit_count(event) for event in events),
                        "totalPullRequestContributions": sum(1 for event in events if event.get("type") == "PullRequestEvent"),
                        "contributionCalendar": {
                            "totalContributions": len(events),
                            "weeks": weeks,
                        },
                    },
                    "repositories": {"nodes": repo_nodes},
                    "pullRequests": {"totalCount": sum(1 for event in events if event.get("type") == "PullRequestEvent")},
                }
            },
        }

    async def _build_public_repositories(self, client: httpx.AsyncClient, username: str, repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        for repo in repos:
            owner = repo.get("owner", {}).get("login") or username
            name = repo.get("name")
            if not name:
                continue

            languages = await self._fetch_repo_languages(client, owner, name)
            total_commits = await self._fetch_commit_count(client, owner, name, repo.get("default_branch"))
            nodes.append(
                {
                    "name": name,
                    "nameWithOwner": repo.get("full_name") or f"{owner}/{name}",
                    "description": repo.get("description"),
                    "stargazerCount": int(repo.get("stargazers_count") or 0),
                    "forkCount": int(repo.get("forks_count") or 0),
                    "primaryLanguage": {"name": repo.get("language")} if repo.get("language") else None,
                    "languages": {
                        "edges": [
                            {"size": int(size), "node": {"name": language}}
                            for language, size in sorted(languages.items(), key=lambda item: item[1], reverse=True)[:5]
                        ]
                    },
                    "defaultBranchRef": {
                        "target": {
                            "history": {"totalCount": total_commits},
                        }
                    },
                }
            )
        return nodes

    async def _fetch_repo_languages(self, client: httpx.AsyncClient, owner: str, repo: str) -> dict[str, int]:
        response = await client.get(f"/repos/{owner}/{repo}/languages")
        if response.status_code >= 400:
            return {}
        return {str(language): int(size) for language, size in response.json().items()}

    async def _fetch_commit_count(self, client: httpx.AsyncClient, owner: str, repo: str, branch: str | None) -> int:
        if not settings.github_fetch_commit_counts:
            return 0
        params: dict[str, Any] = {"per_page": 1}
        if branch:
            params["sha"] = branch
        response = await client.get(f"/repos/{owner}/{repo}/commits", params=params)
        if response.status_code >= 400:
            return 0
        return _extract_total_count(response, len(response.json()))


def _event_commit_count(event: dict[str, Any]) -> int:
    if event.get("type") != "PushEvent":
        return 0
    return len(event.get("payload", {}).get("commits", []))


def _weeks_from_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    today = datetime.now(UTC).date()
    start = today - timedelta(days=55)
    counts: dict[str, int] = {}
    for event in events:
        created_at = event.get("created_at")
        if not created_at:
            continue
        try:
            day = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
        except ValueError:
            continue
        if day >= start:
            counts[day.isoformat()] = counts.get(day.isoformat(), 0) + 1

    weeks: list[dict[str, Any]] = []
    for offset in range(0, 56, 7):
        days = []
        for day_offset in range(7):
            date = start + timedelta(days=offset + day_offset)
            days.append({"date": date.isoformat(), "contributionCount": counts.get(date.isoformat(), 0)})
        weeks.append({"contributionDays": days})
    return weeks
