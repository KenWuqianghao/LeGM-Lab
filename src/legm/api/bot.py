"""Bot control API endpoints."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/bot", tags=["bot"])


class BotStatusResponse(BaseModel):
    """Current bot status."""

    running: bool
    dry_run: bool
    monthly_tweets: int
    monthly_budget: int


@router.get(
    "/status",
    response_model=BotStatusResponse,
    summary="Get bot status",
    description="Returns current bot running state and tweet budget usage.",
)
async def bot_status(request: Request) -> BotStatusResponse:
    """Return current bot status."""
    bot = getattr(request.app.state, "bot", None)
    repo = request.app.state.take_repository
    settings = request.app.state.settings

    monthly_tweets = await repo.get_monthly_tweet_count()

    return BotStatusResponse(
        running=bot is not None and bot.is_running,
        dry_run=settings.bot_dry_run,
        monthly_tweets=monthly_tweets,
        monthly_budget=settings.bot_monthly_budget,
    )


@router.post(
    "/start",
    summary="Start the bot",
    description="Start the LeGM bot's reactive and proactive loops.",
)
async def bot_start(request: Request) -> dict[str, str]:
    """Start the bot."""
    bot = getattr(request.app.state, "bot", None)
    if bot is None:
        return {"status": "error", "message": "Bot not configured"}
    if bot.is_running:
        return {"status": "already_running"}
    bot.start()
    return {"status": "started"}


@router.post(
    "/stop",
    summary="Stop the bot",
    description="Stop the LeGM bot gracefully.",
)
async def bot_stop(request: Request) -> dict[str, str]:
    """Stop the bot."""
    bot = getattr(request.app.state, "bot", None)
    if bot is None:
        return {"status": "error", "message": "Bot not configured"}
    if not bot.is_running:
        return {"status": "already_stopped"}
    await bot.stop()
    return {"status": "stopped"}
