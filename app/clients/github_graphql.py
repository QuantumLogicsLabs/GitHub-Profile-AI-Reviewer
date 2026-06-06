from __future__ import annotations

from typing import Any
import json
from pathlib import Path

import httpx

from app.clients.queries import ANALYZE_PROFILE_QUERY
from app.core.config import settings


class GitHubAPIError(RuntimeError):
    pass


class GitHubGraphQLClient:
    async def analyze_user(self, username: str) -> dict[str, Any]:
        # If token missing, use local sample so app can run offline for testing.
        if not settings.github_token:
            sample_path = Path(__file__).with_name("sample_user.json")
            if sample_path.exists():
                with sample_path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            raise GitHubAPIError("Missing GITHUB_TOKEN in environment and no sample_user.json available.")

        headers = {"Authorization": f"Bearer {settings.github_token}", "Accept": "application/vnd.github+json"}
        payload = {"query": ANALYZE_PROFILE_QUERY, "variables": {"username": username}}

        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(settings.github_api_url, headers=headers, json=payload)

        if response.status_code >= 400:
            raise GitHubAPIError(f"GitHub API status={response.status_code}: {response.text}")

        data = response.json()
        if data.get("errors"):
            raise GitHubAPIError(str(data["errors"]))
        if data.get("data", {}).get("user") is None:
            raise GitHubAPIError(f"GitHub user '{username}' not found.")

        return data
