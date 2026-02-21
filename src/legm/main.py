"""FastAPI application factory with lifespan management."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from legm.agent.analyzer import TakeAnalyzer
from legm.api.router import root_router
from legm.config import Settings, settings
from legm.db.engine import create_async_engine_from_url, create_session_factory
from legm.db.models import Base
from legm.db.repository import TakeRepository
from legm.llm.factory import create_llm_provider
from legm.stats.cache import TTLCache
from legm.stats.client import NBAClient
from legm.stats.service import NBAStatsService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize and tear down application resources."""
    app_settings: Settings = app.state.settings

    # Database
    engine = create_async_engine_from_url(app_settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = create_session_factory(engine)

    # Services
    llm = create_llm_provider(app_settings)
    nba_client = NBAClient()
    cache = TTLCache()
    stats_service = NBAStatsService(nba_client, cache)

    # Wire up app state
    app.state.take_repository = TakeRepository(session_factory)
    app.state.take_analyzer = TakeAnalyzer(llm, stats_service)

    logger.info("LeGM Lab started (provider=%s)", app_settings.llm_provider)
    yield

    # Cleanup
    await engine.dispose()
    logger.info("LeGM Lab shut down")


def create_app(app_settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if app_settings is None:
        app_settings = settings

    app = FastAPI(
        title="LeGM Lab",
        description="LLM-powered NBA take analysis and roasting bot",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.include_router(root_router)

    # Static files for generated charts
    charts_dir = Path("charts")
    charts_dir.mkdir(exist_ok=True)
    app.mount("/charts", StaticFiles(directory=str(charts_dir)), name="charts")

    return app


app = create_app()
