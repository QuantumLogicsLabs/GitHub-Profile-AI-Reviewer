from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.clients.github_graphql import GitHubAPIError
from app.schemas import AnalyzeRequest, AnalyzeResponse, OrgAnalyzeRequest, OrgAnalyzeResponse
from app.service import AnalyzerService

router = APIRouter()
service: AnalyzerService | None = None


def get_service() -> AnalyzerService:
    global service
    if service is None:
        service = AnalyzerService()
    return service


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return await get_service().analyze(payload.username)
    except GitHubAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/analyze-org", response_model=OrgAnalyzeResponse)
async def analyze_org(payload: OrgAnalyzeRequest) -> OrgAnalyzeResponse:
    """Batch org-level hiring pipeline: runs the existing /analyze pipeline
    over every member of an org and returns a combined, ranked report.
    """
    try:
        return await get_service().analyze_org(payload.org, max_members=payload.max_members)
    except GitHubAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc