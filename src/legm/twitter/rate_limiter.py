"""Rate limiting for Twitter bot posting."""

import logging
import time
from collections import deque

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding-window rate limiter with a monthly budget cap.

    Enforces two constraints:
    - A sliding window of ``max_per_window`` posts within ``window_seconds``.
    - A hard ``monthly_budget`` ceiling for total posts in the calendar month.
    """

    def __init__(
        self,
        max_per_window: int = 15,
        window_seconds: int = 900,
        monthly_budget: int = 450,
    ) -> None:
        self._max_per_window = max_per_window
        self._window_seconds = window_seconds
        self._monthly_budget = monthly_budget

        self._timestamps: deque[float] = deque()
        self._monthly_count: int = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def can_post(self) -> bool:
        """Check whether posting is allowed under both rate limits.

        Returns:
            True if the bot may post right now.
        """
        self._purge_expired()

        if self._monthly_count >= self._monthly_budget:
            logger.warning(
                "Monthly budget exhausted (%d/%d)",
                self._monthly_count,
                self._monthly_budget,
            )
            return False

        if len(self._timestamps) >= self._max_per_window:
            logger.debug(
                "Sliding window full (%d/%d)",
                len(self._timestamps),
                self._max_per_window,
            )
            return False

        return True

    def record_post(self) -> None:
        """Record that a post was made right now."""
        now = time.monotonic()
        self._timestamps.append(now)
        self._monthly_count += 1
        logger.debug(
            "Recorded post — window: %d/%d, month: %d/%d",
            len(self._timestamps),
            self._max_per_window,
            self._monthly_count,
            self._monthly_budget,
        )

    @property
    def monthly_count(self) -> int:
        """Current month's post count."""
        return self._monthly_count

    def set_monthly_count(self, count: int) -> None:
        """Set the monthly count, typically loaded from the database on startup.

        Args:
            count: The number of posts already made this month.
        """
        self._monthly_count = count
        logger.info("Monthly count initialized to %d", count)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _purge_expired(self) -> None:
        """Remove timestamps outside the sliding window."""
        cutoff = time.monotonic() - self._window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()
