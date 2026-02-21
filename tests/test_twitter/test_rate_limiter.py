"""Tests for the RateLimiter sliding-window and monthly budget logic."""

from legm.twitter.rate_limiter import RateLimiter


class TestCanPost:
    """Tests for RateLimiter.can_post."""

    def test_can_post_when_under_limits(self) -> None:
        """Should return True when no posts have been made."""
        limiter = RateLimiter(max_per_window=5, window_seconds=60, monthly_budget=100)
        assert limiter.can_post() is True

    def test_cannot_post_when_window_full(self) -> None:
        """Should return False when the sliding window is full."""
        limiter = RateLimiter(max_per_window=3, window_seconds=60, monthly_budget=100)

        for _ in range(3):
            limiter.record_post()

        assert limiter.can_post() is False

    def test_cannot_post_when_monthly_budget_exhausted(self) -> None:
        """Should return False when the monthly budget is used up."""
        limiter = RateLimiter(max_per_window=1000, window_seconds=60, monthly_budget=5)
        limiter.set_monthly_count(5)

        assert limiter.can_post() is False

    def test_can_post_after_partial_usage(self) -> None:
        """Should return True when some posts remain in both window and budget."""
        limiter = RateLimiter(max_per_window=10, window_seconds=60, monthly_budget=100)
        limiter.record_post()
        limiter.record_post()

        assert limiter.can_post() is True


class TestRecordPost:
    """Tests for RateLimiter.record_post."""

    def test_record_post_increments_monthly_count(self) -> None:
        """Each record_post call should increment monthly_count by one."""
        limiter = RateLimiter()

        assert limiter.monthly_count == 0
        limiter.record_post()
        assert limiter.monthly_count == 1
        limiter.record_post()
        assert limiter.monthly_count == 2

    def test_set_monthly_count_initializes_count(self) -> None:
        """set_monthly_count should set the monthly counter to the given value."""
        limiter = RateLimiter()
        limiter.set_monthly_count(42)

        assert limiter.monthly_count == 42
