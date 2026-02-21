"""Tests for the health check endpoint."""

from httpx import ASGITransport, AsyncClient

from legm.config import Settings
from legm.main import create_app


async def test_health_returns_ok() -> None:
    """GET /health should return 200 with {"status": "ok"}."""
    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:"))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
