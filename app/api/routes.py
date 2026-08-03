from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.ai.vector_store import vector_store
from app.clients.github_graphql import GitHubAPIError
from app.schemas import AnalyzeRequest, AnalyzeResponse, OrgAnalyzeRequest, OrgAnalyzeResponse, SimilarDeveloper, SimilarDevelopersResponse
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


@router.get("/similar/{username}", response_model=SimilarDevelopersResponse)
async def similar_developers(
    username: str,
    top_n: int = Query(default=10, ge=1, le=50, description="Number of similar developers to return"),
) -> SimilarDevelopersResponse:
    """Return the *top_n* developers most similar to *username* by embedding cosine similarity.

    The username must have been previously analysed via POST /analyze so that
    its embedding is stored.  Similarity scores are cosine similarity (0–1).

    Args:
        username: GitHub username to use as the search query.
        top_n: How many results to return (1–50, default 10).

    Raises:
        404: If *username* has no stored embedding (never been analysed).
        400: If fewer than 2 profiles are indexed (search is not meaningful).
    """
    if vector_store.count < 2:
        raise HTTPException(
            status_code=400,
            detail="Not enough profiles indexed yet. Analyse at least 2 developers first.",
        )

    try:
        results = vector_store.find_similar(username, top_n=top_n)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"No stored embedding for '{username}'. Analyse this profile first via POST /analyze.",
        )

    return SimilarDevelopersResponse(
        username=username,
        similar=[SimilarDeveloper(username=r.username, similarity=r.similarity) for r in results],
        total_indexed=vector_store.count,
    )
