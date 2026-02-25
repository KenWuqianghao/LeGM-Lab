"""Take analysis API endpoints."""

import hashlib
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
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


def _save_chart(chart_png: bytes, take_id: int, request: Request) -> str:
    """Save chart PNG to disk and return its public URL."""
    CHARTS_DIR.mkdir(exist_ok=True)
    digest = hashlib.sha256(chart_png[:256]).hexdigest()[:8]
    filename = f"take_{take_id}_{digest}.png"
    chart_path = CHARTS_DIR / filename
    chart_path.write_bytes(chart_png)
    return str(request.url_for("charts", path=filename))
