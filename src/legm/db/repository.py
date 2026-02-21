"""Repository layer for database operations."""

from datetime import UTC, datetime

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from legm.db.models import BotConfig, Take, Tweet


class TakeRepository:
    """Async repository for Take, Tweet, and BotConfig operations."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(
        self,
        take_text: str,
        verdict: str,
        confidence: float,
        roast: str,
        reasoning: str,
        stats_used: dict,  # type: ignore[type-arg]
        source_tweet_id: str | None = None,
    ) -> Take:
        """Create and persist a new take.

        Args:
            take_text: The original NBA take text.
            verdict: The verdict label (e.g. "correct", "wrong").
            confidence: Confidence score between 0 and 1.
            roast: Generated roast text.
            reasoning: Explanation of the verdict.
            stats_used: Dictionary of stats referenced in the analysis.
            source_tweet_id: Optional tweet ID that sourced this take.

        Returns:
            The persisted Take instance.
        """
        take = Take(
            take_text=take_text,
            verdict=verdict,
            confidence=confidence,
            roast=roast,
            reasoning=reasoning,
            stats_used=stats_used,
            source_tweet_id=source_tweet_id,
        )
        async with self._session_factory() as session:
            session.add(take)
            await session.commit()
            await session.refresh(take)
        return take

    async def get(self, take_id: int) -> Take | None:
        """Fetch a single take by ID.

        Args:
            take_id: Primary key of the take.

        Returns:
            The Take instance, or None if not found.
        """
        async with self._session_factory() as session:
            return await session.get(Take, take_id)

    async def list_recent(self, limit: int = 50, offset: int = 0) -> list[Take]:
        """List takes ordered by creation date, newest first.

        Args:
            limit: Maximum number of takes to return.
            offset: Number of takes to skip.

        Returns:
            List of Take instances.
        """
        stmt = select(Take).order_by(Take.created_at.desc()).limit(limit).offset(offset)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def record_tweet(
        self,
        take_id: int,
        tweet_id: str,
        tweet_type: str,
        content: str,
    ) -> Tweet:
        """Record a tweet posted for a take.

        Args:
            take_id: Foreign key to the parent take.
            tweet_id: Twitter's unique tweet identifier.
            tweet_type: Either ``"reply"`` or ``"quote_tweet"``.
            content: Full text content of the tweet.

        Returns:
            The persisted Tweet instance.
        """
        tweet = Tweet(
            take_id=take_id,
            tweet_id=tweet_id,
            tweet_type=tweet_type,
            content=content,
        )
        async with self._session_factory() as session:
            session.add(tweet)
            await session.commit()
            await session.refresh(tweet)
        return tweet

    async def get_monthly_tweet_count(self) -> int:
        """Count tweets created in the current calendar month.

        Returns:
            Number of tweets posted this month.
        """
        now = datetime.now(UTC)
        stmt = select(func.count(Tweet.id)).where(
            extract("year", Tweet.created_at) == now.year,
            extract("month", Tweet.created_at) == now.month,
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return result.scalar_one()

    async def get_config(self, key: str) -> str | None:
        """Retrieve a bot configuration value by key.

        Args:
            key: The configuration key to look up.

        Returns:
            The configuration value, or None if the key does not exist.
        """
        stmt = select(BotConfig.value).where(BotConfig.key == key)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def set_config(self, key: str, value: str) -> None:
        """Insert or update a bot configuration entry.

        Args:
            key: The configuration key.
            value: The value to store.
        """
        async with self._session_factory() as session:
            stmt = select(BotConfig).where(BotConfig.key == key)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if config is not None:
                config.value = value
                config.updated_at = datetime.now(UTC)
            else:
                config = BotConfig(key=key, value=value)
                session.add(config)

            await session.commit()
