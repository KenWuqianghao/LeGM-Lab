"""CLI entrypoint for the LeGM bot + API server."""

import asyncio
import logging
import os
import signal
import sys

import uvicorn

from legm.agent.analyzer import TakeAnalyzer
from legm.config import settings
from legm.db.engine import create_async_engine_from_url, create_session_factory
from legm.db.models import Base
from legm.db.repository import TakeRepository
from legm.llm.factory import create_llm_provider
from legm.stats.cache import TTLCache
from legm.stats.client import NBAClient
from legm.stats.service import NBAStatsService
from legm.twitter.bot import LeGMBot
from legm.twitter.filters import TweetFilter
from legm.twitter.rate_limiter import RateLimiter
from legm.twitter.service import TwitterService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("legm.bot")


async def main() -> None:
    """Initialize services, start the bot and the API server."""
    logger.info("Starting LeGM Bot (dry_run=%s)", settings.bot_dry_run)
    logger.info("Database URL: %s", settings.database_url)

    # Database
    engine = create_async_engine_from_url(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = create_session_factory(engine)
    repo = TakeRepository(session_factory)

    # Services
    llm = create_llm_provider(settings)
    stats_service = NBAStatsService(NBAClient(), TTLCache())
    analyzer = TakeAnalyzer(
        llm,
        stats_service,
        simple_mode=settings.bot_simple_analysis,
        exa_api_key=settings.exa_api_key,
    )

    twitter_service = TwitterService(
        bearer_token=settings.twitter_bearer_token,
        api_key=settings.twitter_api_key,
        api_secret=settings.twitter_api_secret,
        access_token=settings.twitter_access_token,
        access_token_secret=settings.twitter_access_token_secret,
    )

    tweet_filter = TweetFilter()
    rate_limiter = RateLimiter(monthly_budget=settings.bot_monthly_budget)

    # Load persisted monthly count
    monthly_count = await repo.get_monthly_tweet_count()
    rate_limiter.set_monthly_count(monthly_count)

    bot = LeGMBot(
        twitter_service=twitter_service,
        take_analyzer=analyzer,
        take_repository=repo,
        tweet_filter=tweet_filter,
        rate_limiter=rate_limiter,
        settings=settings,
    )

    # Graceful shutdown
    stop_event = asyncio.Event()

    def _handle_signal() -> None:
        logger.info("Received shutdown signal")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal)

    bot.start()
    logger.info("Bot is running. Press Ctrl+C to stop.")

    # Start the FastAPI server alongside the bot
    port = int(os.environ.get("PORT", "8000"))
    config = uvicorn.Config(
        "legm.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve(), name="legm-api")
    logger.info("API server starting on port %d", port)

    await stop_event.wait()
    server.should_exit = True
    await server_task
    await bot.stop()
    await engine.dispose()
    logger.info("Bot and API server stopped cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
