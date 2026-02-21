"""Database engine and session factory configuration."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_async_engine_from_url(url: str) -> AsyncEngine:
    """Create a SQLAlchemy async engine from a database URL.

    Args:
        url: Database connection URL (e.g. ``sqlite+aiosqlite:///./legm.db``).

    Returns:
        Configured async engine instance.
    """
    return create_async_engine(
        url,
        echo=False,
        pool_pre_ping=True,
    )


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the given engine.

    Args:
        engine: The async engine to bind sessions to.

    Returns:
        Session factory that produces ``AsyncSession`` instances.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
