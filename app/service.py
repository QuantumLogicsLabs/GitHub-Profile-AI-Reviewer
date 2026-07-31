from __future__ import annotations

import asyncio

from app.clients.github_graphql import fetch_org_members
from app.graph.workflow import AnalyzerWorkflow
from app.schemas import AnalyzeResponse, OrgAnalyzeResponse, OrgMemberError


class AnalyzerService:
    def __init__(self) -> None:
        self._workflow = AnalyzerWorkflow()

    async def analyze(self, username: str) -> AnalyzeResponse:
        state = await self._workflow.run(username)
        return AnalyzeResponse.model_validate(state["final_report"])

    async def analyze_org(
        self,
        org: str,
        max_members: int | None = None,
        concurrency: int = 5,
    ) -> OrgAnalyzeResponse:
        """Run the existing analyze() pipeline over every member of an org and
        return a combined, ranked report. Reuses analyze() as-is; does not
        implement any new scoring logic.
        """
        members = await fetch_org_members(org, max_members=max_members)

        semaphore = asyncio.Semaphore(concurrency)
        results: list[AnalyzeResponse] = []
        failures: list[OrgMemberError] = []

        async def _analyze_one(username: str) -> None:
            async with semaphore:
                try:
                    result = await self.analyze(username)
                    results.append(result)
                except Exception as exc:  # noqa: BLE001 - one member failing shouldn't fail the batch
                    failures.append(OrgMemberError(username=username, error=str(exc)))

        await asyncio.gather(*(_analyze_one(username) for username in members))

        ranked_results = sorted(results, key=lambda r: r.rating_score, reverse=True)

        return OrgAnalyzeResponse(
            org=org,
            total_members=len(members),
            analyzed_count=len(ranked_results),
            failed_count=len(failures),
            ranked_results=ranked_results,
            failures=failures,
        )