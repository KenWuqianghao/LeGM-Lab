"""Shared pytest fixtures for the LeGM test suite."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from legm.agent.analyzer import TakeAnalyzer
from legm.config import LLMProvider as LLMProviderEnum
from legm.config import Settings
from legm.db.engine import create_async_engine_from_url, create_session_factory
from legm.db.models import Base
from legm.db.repository import TakeRepository
from legm.llm.types import LLMResponse
from legm.stats.cache import TTLCache
from legm.stats.client import NBAClient
from legm.stats.service import NBAStatsService


@pytest.fixture()
def mock_llm_provider() -> AsyncMock:
    """A mock implementing LLMProvider that returns a configurable LLMResponse.

    The default response has empty content, no tool calls, and ``"end_turn"``
    stop reason.  Override via ``mock_llm_provider.generate.return_value``.
    """
    provider = AsyncMock()
    provider.generate.return_value = LLMResponse(
        content="",
        tool_calls=[],
        stop_reason="end_turn",
    )
    return provider


@pytest.fixture()
def stats_service() -> NBAStatsService:
    """An NBAStatsService backed by a mock NBAClient."""
    mock_client = MagicMock(spec=NBAClient)
    # Make async methods return AsyncMock so they can be awaited
    mock_client.get_player_stats = AsyncMock(return_value={})
    mock_client.get_player_game_log = AsyncMock(return_value=[])
    mock_client.get_team_standings = AsyncMock(return_value=[])
    cache = TTLCache(default_ttl=0)
    return NBAStatsService(client=mock_client, cache=cache)


@pytest.fixture()
def take_analyzer(
    mock_llm_provider: AsyncMock,
    stats_service: NBAStatsService,
) -> TakeAnalyzer:
    """A TakeAnalyzer wired to the mock LLM provider and mock stats service."""
    return TakeAnalyzer(llm=mock_llm_provider, stats_service=stats_service)


@pytest.fixture()
async def db_session_factory() -> AsyncGenerator[
    async_sessionmaker[AsyncSession], None
]:
    """Async session factory backed by an in-memory SQLite database.

    Creates all tables before yielding, and disposes of the engine on teardown.
    """
    engine = create_async_engine_from_url("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = create_session_factory(engine)
    yield factory

    await engine.dispose()


@pytest.fixture()
async def take_repository(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> TakeRepository:
    """A TakeRepository using the in-memory SQLite database."""
    return TakeRepository(session_factory=db_session_factory)


@pytest.fixture()
def test_settings() -> Settings:
    """Settings instance with safe test defaults."""
    return Settings(
        llm_provider=LLMProviderEnum.CLAUDE,
        llm_model="test-model",
        anthropic_api_key="test-anthropic-key",
        openai_api_key="test-openai-key",
        openai_compat_base_url="http://localhost:8000/v1",
        openai_compat_api_key="test-compat-key",
        database_url="sqlite+aiosqlite:///:memory:",
        twitter_bearer_token="test-bearer",
        twitter_api_key="test-api-key",
        twitter_api_secret="test-api-secret",
        twitter_access_token="test-access-token",
        twitter_access_token_secret="test-access-secret",
        twitter_bot_user_id="12345",
        bot_dry_run=True,
    )
