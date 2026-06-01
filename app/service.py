from __future__ import annotations

from app.graph.workflow import AnalyzerWorkflow
from app.schemas import AnalyzeResponse


class AnalyzerService:
    def __init__(self) -> None:
        self._workflow = AnalyzerWorkflow()

    async def analyze(self, username: str) -> AnalyzeResponse:
        state = await self._workflow.run(username)
        return AnalyzeResponse.model_validate(state["final_report"])
