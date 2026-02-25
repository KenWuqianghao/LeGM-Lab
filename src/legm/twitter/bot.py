"""LeGMBot orchestrator — reactive and proactive tweet loops."""

import asyncio
import contextlib
import logging
from typing import Any

from legm.agent.analyzer import TakeAnalyzer
from legm.config import Settings
from legm.db.repository import TakeRepository
from legm.twitter.filters import TweetFilter
from legm.twitter.rate_limiter import RateLimiter
from legm.twitter.service import TwitterService

logger = logging.getLogger(__name__)


class LeGMBot:
    """Main bot orchestrator that runs reactive and proactive tweet loops.

    The reactive loop polls for mentions and replies with analysis.
    The proactive loop searches for NBA takes and quote-tweets them.
    Both loops respect rate limits and can operate in dry-run mode.
    """

    def __init__(
        self,
        twitter_service: TwitterService,
        take_analyzer: TakeAnalyzer,
        take_repository: TakeRepository,
        tweet_filter: TweetFilter,
        rate_limiter: RateLimiter,
        settings: Settings,
    ) -> None:
        self._twitter = twitter_service
        self._analyzer = take_analyzer
        self._repository = take_repository
        self._filter = tweet_filter
        self._rate_limiter = rate_limiter
        self._settings = settings

        self._reactive_task: asyncio.Task[None] | None = None
        self._proactive_task: asyncio.Task[None] | None = None
        self._running = False
        self._since_id: str | None = None
        self._daily_proactive_count = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """Whether the bot loops are currently active."""
        return self._running

    def start(self) -> None:
        """Start the reactive and proactive loops as background tasks."""
        if self._running:
            logger.warning("Bot is already running")
            return

        self._running = True
        self._reactive_task = asyncio.create_task(
            self._reactive_loop(),
            name="legm-reactive",
        )
        self._proactive_task = asyncio.create_task(
            self._proactive_loop(),
            name="legm-proactive",
        )
        logger.info("LeGMBot started (dry_run=%s)", self._settings.bot_dry_run)

    async def stop(self) -> None:
        """Cancel running tasks and shut down the bot."""
        self._running = False

        for task in (self._reactive_task, self._proactive_task):
            if task is not None and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        self._reactive_task = None
        self._proactive_task = None
        logger.info("LeGMBot stopped")

    # ------------------------------------------------------------------
    # Reactive loop — reply to mentions
    # ------------------------------------------------------------------

    async def _reactive_loop(self) -> None:
        """Poll for mentions and reply with take analysis."""
        # Load persisted since_id on first run
        stored = await self._repository.get_config("mentions_since_id")
        if stored is not None:
            self._since_id = stored
            logger.info("Resuming mentions from since_id=%s", self._since_id)

        while self._running:
            try:
                await self._process_mentions()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Error in reactive loop iteration")

            await asyncio.sleep(self._settings.bot_mention_poll_interval)

    async def _process_mentions(self) -> None:
        """Fetch and handle new mentions."""
        mentions = await self._twitter.get_mentions(
            user_id=self._settings.twitter_bot_user_id,
            since_id=self._since_id,
        )

        if not mentions:
            return

        logger.info("Processing %d mentions", len(mentions))

        for mention in mentions:
            try:
                await self._handle_mention(mention)
            except Exception:
                logger.exception(
                    "Failed to handle mention %s",
                    mention.get("id"),
                )

            # Track the newest mention ID regardless of success
            mention_id = mention.get("id")
            if mention_id and (
                self._since_id is None or int(mention_id) > int(self._since_id)
            ):
                self._since_id = mention_id
                await self._repository.set_config("mentions_since_id", self._since_id)

    async def _handle_mention(self, mention: dict[str, Any]) -> None:
        """Analyze a single mention and reply."""
        if self._filter.should_skip(mention, is_mention=True):
            return

        if not self._rate_limiter.can_post():
            logger.warning("Rate limit reached, skipping mention %s", mention["id"])
            return

        take_text = mention["text"]
        analysis = await self._analyzer.analyze(take_text)

        # Persist the take
        take = await self._repository.create(
            take_text=take_text,
            verdict=analysis.verdict,
            confidence=analysis.confidence,
            roast=analysis.roast,
            reasoning=analysis.reasoning,
            stats_used={"stats": analysis.stats_used},
            source_tweet_id=mention["id"],
        )

        if self._settings.bot_dry_run:
            logger.info(
                "[DRY RUN] Would reply to %s: %s",
                mention["id"],
                analysis.roast,
            )
            return

        if analysis.chart_png:
            tweet_id = await self._twitter.post_tweet_with_media(
                text=analysis.roast,
                image_bytes=analysis.chart_png,
                in_reply_to_tweet_id=mention["id"],
            )
        else:
            tweet_id = await self._twitter.reply_to_tweet(
                text=analysis.roast,
                in_reply_to_tweet_id=mention["id"],
            )

        self._rate_limiter.record_post()

        await self._repository.record_tweet(
            take_id=take.id,
            tweet_id=tweet_id,
            tweet_type="reply",
            content=analysis.roast,
        )

        logger.info("Replied to mention %s with tweet %s", mention["id"], tweet_id)

    # ------------------------------------------------------------------
    # Proactive loop — search and quote-tweet NBA takes
    # ------------------------------------------------------------------

    async def _proactive_loop(self) -> None:
        """Search for NBA takes and quote-tweet the spiciest ones."""
        while self._running:
            try:
                await self._search_and_engage()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Error in proactive loop iteration")

            await asyncio.sleep(self._settings.bot_search_poll_interval)

    async def _search_and_engage(self) -> None:
        """Run one search cycle: find tweets, pick the best, quote-tweet."""
        if self._daily_proactive_count >= self._settings.bot_max_daily_proactive:
            logger.debug(
                "Daily proactive limit reached (%d/%d)",
                self._daily_proactive_count,
                self._settings.bot_max_daily_proactive,
            )
            return

        if not self._rate_limiter.can_post():
            logger.debug("Rate limit prevents proactive posting")
            return

        # Search with a broad NBA takes query
        query = "NBA take -is:retweet -is:reply lang:en"
        tweets = await self._twitter.search_recent_tweets(
            query=query,
            max_results=20,
        )

        # Filter candidates
        candidates = [t for t in tweets if not self._filter.should_skip(t)]
        if not candidates:
            logger.debug("No viable candidates found in search")
            return

        # Pick the "spiciest" — shortest text is often the boldest take
        best = min(candidates, key=lambda t: len(t.get("text", "")))
        logger.info("Selected proactive target: %s", best["text"][:80])

        take_text = best["text"]
        analysis = await self._analyzer.analyze(take_text)

        # Persist the take
        take = await self._repository.create(
            take_text=take_text,
            verdict=analysis.verdict,
            confidence=analysis.confidence,
            roast=analysis.roast,
            reasoning=analysis.reasoning,
            stats_used={"stats": analysis.stats_used},
            source_tweet_id=best["id"],
        )

        if self._settings.bot_dry_run:
            logger.info(
                "[DRY RUN] Would reply to %s: %s",
                best["id"],
                analysis.roast,
            )
            return

        if analysis.chart_png:
            tweet_id = await self._twitter.post_tweet_with_media(
                text=analysis.roast,
                image_bytes=analysis.chart_png,
                in_reply_to_tweet_id=best["id"],
            )
        else:
            tweet_id = await self._twitter.reply_to_tweet(
                text=analysis.roast,
                in_reply_to_tweet_id=best["id"],
            )

        self._rate_limiter.record_post()
        self._daily_proactive_count += 1

        await self._repository.record_tweet(
            take_id=take.id,
            tweet_id=tweet_id,
            tweet_type="reply",
            content=analysis.roast,
        )

        logger.info(
            "Replied to %s with tweet %s (daily: %d/%d)",
            best["id"],
            tweet_id,
            self._daily_proactive_count,
            self._settings.bot_max_daily_proactive,
        )
