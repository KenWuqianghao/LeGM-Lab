"""Low-level async wrapper around the synchronous nba_api library."""

import asyncio
import logging
import time
from collections.abc import Callable

from nba_api.stats.endpoints import (
    leaguestandings,
    playercareerstats,
    playerestimatedmetrics,
    playergamelog,
)

logger = logging.getLogger(__name__)

# stats.nba.com requires browser-like headers or it will timeout/block.
# These must match nba_api's defaults closely to avoid server-side throttling.
_HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://stats.nba.com/",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

_MAX_RETRIES = 2
_RETRY_DELAYS = [1.0, 3.0]


async def _retry_async[T](
    fn: Callable[[], T],
    label: str = "nba_api",
) -> T:
    """Run a sync callable in a thread with retry on timeout."""
    for attempt in range(_MAX_RETRIES):
        try:
            return await asyncio.to_thread(fn)
        except Exception:
            if attempt == _MAX_RETRIES - 1:
                raise
            delay = _RETRY_DELAYS[attempt]
            logger.warning(
                "%s attempt %d failed, retrying in %.1fs",
                label,
                attempt + 1,
                delay,
            )
            await asyncio.sleep(delay)
    raise RuntimeError("unreachable")  # pragma: no cover


class NBAClient:
    """Thin async facade over ``nba_api.stats.endpoints``.

    Every public method offloads the blocking HTTP call to a thread via
    ``asyncio.to_thread`` and retries on failure with backoff.
    """

    _MIN_REQUEST_INTERVAL: float = 0.6

    def __init__(self) -> None:
        self._last_request_time: float = 0.0

    async def _throttle(self) -> None:
        """Sleep if necessary to respect the per-request rate limit."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._MIN_REQUEST_INTERVAL:
            await asyncio.sleep(self._MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    async def get_player_stats(self, player_id: int, season: str) -> dict:
        """Fetch career stats and extract the requested *season*."""
        await self._throttle()
        career = await _retry_async(
            lambda: playercareerstats.PlayerCareerStats(
                player_id=player_id,
                headers=_HEADERS,
                timeout=30,
            ),
            label=f"PlayerCareerStats({player_id})",
        )
        rows = career.get_normalized_dict()["SeasonTotalsRegularSeason"]
        for row in rows:
            if row.get("SEASON_ID") == season:
                return dict(row)
        return {}

    async def get_player_game_log(
        self,
        player_id: int,
        season: str,
        last_n: int = 10,
    ) -> list[dict]:
        """Return the most recent *last_n* regular-season games."""
        await self._throttle()
        log = await _retry_async(
            lambda: playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                headers=_HEADERS,
                timeout=30,
            ),
            label=f"PlayerGameLog({player_id})",
        )
        rows = log.get_normalized_dict()["PlayerGameLog"]
        return [dict(r) for r in rows[:last_n]]

    async def get_player_estimated_metrics(self, season: str) -> list[dict]:
        """Fetch estimated advanced metrics for all players in a season.

        Returns the full list — caller is responsible for filtering by player.
        """
        await self._throttle()
        metrics = await _retry_async(
            lambda: playerestimatedmetrics.PlayerEstimatedMetrics(
                season=season,
                season_type="Regular Season",
                headers=_HEADERS,
                timeout=30,
            ),
            label=f"PlayerEstimatedMetrics({season})",
        )
        return [
            dict(r) for r in metrics.get_normalized_dict()["PlayerEstimatedMetrics"]
        ]

    async def get_team_standings(self) -> list[dict]:
        """Return current-season league standings for every team."""
        await self._throttle()
        standings = await _retry_async(
            lambda: leaguestandings.LeagueStandings(
                headers=_HEADERS,
                timeout=30,
            ),
            label="LeagueStandings",
        )
        return [dict(r) for r in standings.get_normalized_dict()["Standings"]]
