from __future__ import annotations

from datetime import datetime, timedelta, timezone
UTC = timezone.utc
import time
from typing import Any

import httpx

from app.clients.queries import ANALYZE_PROFILE_QUERY
from app.core.config import settings


class GitHubAPIError(RuntimeError):
    pass


_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _headers(use_token: bool = True) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if use_token and settings.github_token:
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


def _cache_get(key: str) -> dict[str, Any] | None:
    item = _CACHE.get(key)
    if item is None:
        return None
    expires_at, value = item
    if expires_at < time.time():
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: dict[str, Any]) -> dict[str, Any]:
    _CACHE[key] = (time.time() + settings.github_cache_ttl_seconds, value)
    return value


def _github_error(response: httpx.Response) -> GitHubAPIError:
    if response.status_code == 403 and "rate limit" in response.text.lower():
        reset = response.headers.get("X-RateLimit-Reset")
        reset_hint = ""
        if reset and reset.isdigit():
            reset_at = datetime.fromtimestamp(int(reset), tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
            reset_hint = f" Rate limit resets at {reset_at}."
        return GitHubAPIError(
            "GitHub public API rate limit exceeded."
            " Add a valid GITHUB_TOKEN in .env and restart the server, or wait for the limit to reset."
            f"{reset_hint}"
        )
    return GitHubAPIError(f"GitHub API status={response.status_code}: {response.text}")


class GitHubGraphQLClient:
    async def analyze_user(self, username: str) -> dict[str, Any]:
        cache_key = f"github:{username.lower()}:{'graphql' if settings.github_token else 'public'}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        if not settings.github_token:
            return _cache_set(cache_key, await self._analyze_public_user(username))

        payload = {"query": ANALYZE_PROFILE_QUERY, "variables": {"username": username}}

        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(settings.github_api_url, headers=_headers(), json=payload)

        if response.status_code >= 400:
            if response.status_code == 401:
                public_key = f"github:{username.lower()}:public"
                cached_public = _cache_get(public_key)
                if cached_public is not None:
                    return cached_public
                return _cache_set(public_key, await self._analyze_public_user(username, use_token=False))
            raise _github_error(response)

        data = response.json()
        if data.get("errors"):
            raise GitHubAPIError(str(data["errors"]))
        if data.get("data", {}).get("user") is None:
            raise GitHubAPIError(f"GitHub user '{username}' not found.")

        data["source"] = "graphql"
        return _cache_set(cache_key, data)

    async def _analyze_public_user(self, username: str, use_token: bool = False) -> dict[str, Any]:
        base_url = settings.github_rest_api_url.rstrip("/")
        async with httpx.AsyncClient(base_url=base_url, timeout=settings.request_timeout_seconds, headers=_headers(use_token=use_token)) as client:
            user_response = await client.get(f"/users/{username}")
            if user_response.status_code == 404:
                raise GitHubAPIError(f"GitHub user '{username}' not found.")
            if user_response.status_code >= 400:
                raise _github_error(user_response)

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
                raise _github_error(repos_response)

            events_response = await client.get(f"/users/{username}/events/public", params={"per_page": 100})
            events = events_response.json() if events_response.status_code < 400 else []

            user = user_response.json()
            repos = repos_response.json()
            repo_nodes = self._build_public_repositories(username, repos)
            weeks = _weeks_from_events(events)
            public_commits = sum(_event_commit_count(event) for event in events)
            public_prs_created = sum(1 for event in events if _is_pr_created_event(event))

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
                        "totalCommitContributions": public_commits,
                        "totalPullRequestContributions": public_prs_created,
                        "contributionCalendar": {
                            "totalContributions": len(events),
                            "weeks": weeks,
                        },
                    },
                    "repositories": {"nodes": repo_nodes},
                    "pullRequests": {"totalCount": public_prs_created},
                    "publicActivity": {
                        "publicCommits": public_commits,
                        "publicPRsCreated": public_prs_created,
                        "sourceWindow": "recent public events",
                    },
                }
            },
        }

    def _build_public_repositories(self, username: str, repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        for repo in repos:
            owner = repo.get("owner", {}).get("login") or username
            name = repo.get("name")
            if not name:
                continue

            primary_language = repo.get("language")
            repo_size = int(repo.get("size") or 0)
            nodes.append(
                {
                    "name": name,
                    "nameWithOwner": repo.get("full_name") or f"{owner}/{name}",
                    "description": repo.get("description"),
                    "stargazerCount": int(repo.get("stargazers_count") or 0),
                    "forkCount": int(repo.get("forks_count") or 0),
                    "primaryLanguage": {"name": primary_language} if primary_language else None,
                    "languages": {
                        "edges": [
                            {"size": max(repo_size, 1), "node": {"name": primary_language}}
                        ] if primary_language else []
                    },
                    "defaultBranchRef": {
                        "target": {
                            "history": {"totalCount": 0},
                        }
                    },
                    "publicSignals": {
                        "updatedAt": repo.get("updated_at"),
                        "pushedAt": repo.get("pushed_at"),
                        "isFork": bool(repo.get("fork")),
                        "openIssues": int(repo.get("open_issues_count") or 0),
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


def _is_pr_created_event(event: dict[str, Any]) -> bool:
    if event.get("type") != "PullRequestEvent":
        return False
    return event.get("payload", {}).get("action") in {"opened", "reopened"}


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


async def fetch_org_members(org: str, max_members: int | None = None) -> list[str]:
    """Fetch usernames of all members of a GitHub organization.

    Uses the authenticated /orgs/{org}/members endpoint when GITHUB_TOKEN is set
    (returns all members visible to the token). Falls back to the public
    /orgs/{org}/public_members endpoint when no token is configured (returns
    only members who have chosen to make their membership public).
    """
    endpoint = "members" if settings.github_token else "public_members"
    usernames: list[str] = []
    page = 1
    per_page = 100

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        while True:
            response = await client.get(
                f"{settings.github_rest_api_url}/orgs/{org}/{endpoint}",
                headers=_headers(use_token=True),
                params={"per_page": per_page, "page": page},
            )
            if response.status_code != 200:
                raise _github_error(response)

            batch = response.json()
            if not batch:
                break

            usernames.extend(member["login"] for member in batch)

            if max_members is not None and len(usernames) >= max_members:
                usernames = usernames[:max_members]
                break
            if len(batch) < per_page:
                break
            page += 1

    return usernames