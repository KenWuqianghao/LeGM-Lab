"""Tests for the takes analysis API endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from legm.agent.analyzer import TakeAnalysis
from legm.api.router import root_router
from legm.db.engine import create_async_engine_from_url, create_session_factory
from legm.db.models import Base
from legm.db.repository import TakeRepository


@pytest.fixture()
async def takes_app() -> FastAPI:
    """Create a minimal FastAPI app with a real in-memory DB and mocked analyzer.

    Bypasses the full lifespan (which needs LLM credentials) by wiring
    app.state manually with a real TakeRepository and a mock TakeAnalyzer.
    """
    app = FastAPI()
    app.include_router(root_router)

    engine = create_async_engine_from_url("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = create_session_factory(engine)
    app.state.take_repository = TakeRepository(session_factory)
    app.state.take_analyzer = AsyncMock()

    yield app

    await engine.dispose()


async def test_analyze_take_returns_analysis(takes_app: FastAPI) -> None:
    """POST /api/v1/takes/analyze should return a structured analysis."""
    fake_analysis = TakeAnalysis(
        verdict="trash",
        confidence=0.92,
        roast="LeBron isn't washed, your take is.",
        reasoning="LeBron is averaging 25/7/7 this season.",
        stats_used=["season_averages"],
    )
    takes_app.state.take_analyzer.analyze = AsyncMock(return_value=fake_analysis)

    async with AsyncClient(
        transport=ASGITransport(app=takes_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/takes/analyze",
            json={"take": "LeBron is washed and can't carry a team anymore"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "trash"
    assert data["confidence"] == 0.92
    assert data["roast"] == "LeBron isn't washed, your take is."
    assert data["reasoning"] == "LeBron is averaging 25/7/7 this season."
    assert data["stats_used"] == ["season_averages"]
    assert "take_id" in data


async def test_list_takes_returns_empty_list(takes_app: FastAPI) -> None:
    """GET /api/v1/takes should return an empty list when no takes exist."""
    async with AsyncClient(
        transport=ASGITransport(app=takes_app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/takes")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_takes_returns_created_takes(takes_app: FastAPI) -> None:
    """GET /api/v1/takes should return takes that were previously created."""
    fake_analysis = TakeAnalysis(
        verdict="valid",
        confidence=0.85,
        roast="Respect, this take actually checks out.",
        reasoning="Jokic is indeed leading the league in assists among centers.",
        stats_used=["season_averages", "league_leaders"],
    )
    takes_app.state.take_analyzer.analyze = AsyncMock(return_value=fake_analysis)

    async with AsyncClient(
        transport=ASGITransport(app=takes_app),
        base_url="http://test",
    ) as client:
        # Create a take first
        await client.post(
            "/api/v1/takes/analyze",
            json={"take": "Jokic is the best passing center in NBA history"},
        )

        # Now list takes
        response = await client.get("/api/v1/takes")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["verdict"] == "valid"
    assert data[0]["take_text"] == "Jokic is the best passing center in NBA history"
