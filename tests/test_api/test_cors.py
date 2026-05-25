"""Tests for CORS configuration."""

from httpx import ASGITransport, AsyncClient

from legm.config import Settings
from legm.main import create_app


async def test_cors_allows_production_vercel_origin() -> None:
    """Preflight from legm-lab.vercel.app should succeed."""
    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:"))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.options(
            "/api/v1/takes/analyze",
            headers={
                "Origin": "https://legm-lab.vercel.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "https://legm-lab.vercel.app"
    )


async def test_cors_allows_vercel_preview_origin() -> None:
    """Preflight from Vercel preview URLs should succeed."""
    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:"))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "https://legm-lab-git-main-foo.vercel.app",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "https://legm-lab-git-main-foo.vercel.app"
    )
