"""Take analysis API endpoints."""

import hashlib
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from legm.dependencies import TakeAnalyzerDep, TakeRepositoryDep

router = APIRouter(prefix="/api/v1/takes", tags=["takes"])

CHARTS_DIR = Path("charts")


class AnalyzeTakeRequest(BaseModel):
    """Request body for analyzing an NBA take."""

    take: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The NBA take to analyze",
    )


class TakeResponse(BaseModel):
    """Response for a single take analysis."""

    id: int
    take_text: str
    verdict: str
    confidence: float
    roast: str
    reasoning: str
    stats_used: list[str]
    created_at: datetime


class TakeDetailResponse(BaseModel):
    """Response for a single take with chart URL."""

    id: int
    take_text: str
    verdict: str
    confidence: float
    roast: str
    reasoning: str
    stats_used: list[str]
    chart_url: str | None = None
    created_at: datetime


class AnalyzeTakeResponse(BaseModel):
    """Response from the analyze endpoint."""

    verdict: str
    confidence: float
    roast: str
    reasoning: str
    stats_used: list[str]
    take_id: int
    chart_url: str | None = None


@router.post(
    "/analyze",
    response_model=AnalyzeTakeResponse,
    summary="Analyze an NBA take",
    description="Submit an NBA take for analysis. Returns a verdict, roast, and optional chart.",
)
async def analyze_take(
    body: AnalyzeTakeRequest,
    analyzer: TakeAnalyzerDep,
    repo: TakeRepositoryDep,
    request: Request,
) -> AnalyzeTakeResponse:
    """Analyze a take and persist the result."""
    analysis = await analyzer.analyze(body.take)

    take = await repo.create(
        take_text=body.take,
        verdict=analysis.verdict,
        confidence=analysis.confidence,
        roast=analysis.roast,
        reasoning=analysis.reasoning,
        stats_used=analysis.stats_used,
    )

    chart_url: str | None = None
    if analysis.chart_png:
        chart_url = _save_chart(analysis.chart_png, take.id, request)

    return AnalyzeTakeResponse(
        verdict=analysis.verdict,
        confidence=analysis.confidence,
        roast=analysis.roast,
        reasoning=analysis.reasoning,
        stats_used=analysis.stats_used,
        take_id=take.id,
        chart_url=chart_url,
    )


@router.get(
    "/{take_id}",
    response_model=TakeDetailResponse,
    summary="Get a single take analysis",
    description="Retrieve a take by ID, including chart URL if available.",
)
async def get_take(
    take_id: int,
    repo: TakeRepositoryDep,
    request: Request,
) -> TakeDetailResponse:
    """Fetch a single take by ID."""
    take = await repo.get(take_id)
    if take is None:
        raise HTTPException(status_code=404, detail="Take not found")

    chart_url = _find_chart(take.id, request)

    return TakeDetailResponse(
        id=take.id,
        take_text=take.take_text,
        verdict=take.verdict,
        confidence=take.confidence,
        roast=take.roast,
        reasoning=take.reasoning,
        stats_used=take.stats_used or [],
        chart_url=chart_url,
        created_at=take.created_at,
    )


@router.get(
    "",
    response_model=list[TakeResponse],
    summary="List past take analyses",
    description="Retrieve recent take analyses, ordered by most recent first.",
)
async def list_takes(
    repo: TakeRepositoryDep,
    limit: int = 50,
    offset: int = 0,
) -> list[TakeResponse]:
    """List recent take analyses."""
    takes = await repo.list_recent(limit=limit, offset=offset)
    return [
        TakeResponse(
            id=t.id,
            take_text=t.take_text,
            verdict=t.verdict,
            confidence=t.confidence,
            roast=t.roast,
            reasoning=t.reasoning,
            stats_used=t.stats_used or [],
            created_at=t.created_at,
        )
        for t in takes
    ]


def _find_chart(take_id: int, request: Request) -> str | None:
    """Look up an existing chart PNG for a take."""
    matches = list(CHARTS_DIR.glob(f"take_{take_id}_*.png"))
    if not matches:
        return None
    return str(request.url_for("charts", path=matches[0].name))


def _save_chart(chart_png: bytes, take_id: int, request: Request) -> str:
    """Save chart PNG to disk and return its public URL."""
    CHARTS_DIR.mkdir(exist_ok=True)
    digest = hashlib.sha256(chart_png[:256]).hexdigest()[:8]
    filename = f"take_{take_id}_{digest}.png"
    chart_path = CHARTS_DIR / filename
    chart_path.write_bytes(chart_png)
    return str(request.url_for("charts", path=filename))
