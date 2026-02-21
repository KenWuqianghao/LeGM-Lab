"""SQLAlchemy ORM models for the LeGM database."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Take(Base):
    """A scored NBA take with verdict, roast, and reasoning."""

    __tablename__ = "takes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    take_text: Mapped[str] = mapped_column(Text, nullable=False)
    verdict: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    roast: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    stats_used: Mapped[dict] = mapped_column(JSON, nullable=False)  # type: ignore[type-arg]
    source_tweet_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    tweets: Mapped[list["Tweet"]] = relationship(
        "Tweet", back_populates="take", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Take id={self.id} verdict={self.verdict!r}>"


class Tweet(Base):
    """A tweet posted by the bot in response to a take."""

    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    take_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("takes.id"), nullable=False
    )
    tweet_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    tweet_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "reply" | "quote_tweet"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retweets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    take: Mapped["Take"] = relationship("Take", back_populates="tweets")

    def __repr__(self) -> str:
        return f"<Tweet id={self.id} tweet_id={self.tweet_id!r}>"


class BotConfig(Base):
    """Key-value configuration store for the bot."""

    __tablename__ = "bot_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<BotConfig key={self.key!r}>"
