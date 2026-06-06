from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.clients.github_graphql import GitHubAPIError
from app.core.config import settings
from app.core.logging import setup_logging
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.service import AnalyzerService

setup_logging()

app = FastAPI(title=settings.app_name, version=settings.app_version)
service: AnalyzerService | None = None


def get_service() -> AnalyzerService:
    global service
    if service is None:
        service = AnalyzerService()
    return service


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return await get_service().analyze(payload.username)
    except GitHubAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
