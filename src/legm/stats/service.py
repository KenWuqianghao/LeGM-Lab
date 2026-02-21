"""High-level async service for NBA stats queries."""

from legm.stats.cache import TTLCache
from legm.stats.client import NBAClient
from legm.stats.models import (
    PlayerAdvancedStats,
    PlayerComparisonResult,
    PlayerGameLog,
    PlayerSeasonStats,
    TeamStanding,
)
from legm.stats.utils import find_player_id, get_current_season


class NBAStatsService:
    """Orchestrates player / team lookups with caching and model parsing.

    Usage::

        client = NBAClient()
        cache = TTLCache(default_ttl=3600)
        svc = NBAStatsService(client, cache)

        stats = await svc.get_player_season_averages("LeBron James")
    """

    def __init__(self, client: NBAClient, cache: TTLCache) -> None:
        self._client = client
        self._cache = cache

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_player(self, name: str) -> tuple[int, str]:
        """Return ``(player_id, canonical_name)`` or raise ``ValueError``."""
        player_id = find_player_id(name)
        if player_id is None:
            raise ValueError(
                f"Could not find an NBA player matching '{name}'. "
                "Try using their full name (e.g. 'LeBron James')."
            )
        return player_id, name.strip()

    @staticmethod
    def _season_or_current(season: str | None) -> str:
        return season if season is not None else get_current_season()

    # ------------------------------------------------------------------
    # Player season averages
    # ------------------------------------------------------------------

    async def get_player_season_averages(
        self,
        player_name: str,
        season: str | None = None,
    ) -> PlayerSeasonStats:
        """Get per-game averages for a player in the given (or current) season."""
        player_id, name = self._resolve_player(player_name)
        season = self._season_or_current(season)
        cache_key = f"player_season:{player_id}:{season}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        raw = await self._client.get_player_stats(player_id, season)
        if not raw:
            raise ValueError(f"No stats found for '{name}' in the {season} season.")

        gp = raw["GP"]
        model = PlayerSeasonStats(
            player_name=name,
            player_id=player_id,
            season=season,
            team=raw.get("TEAM_ABBREVIATION", ""),
            games_played=gp,
            mpg=round(raw["MIN"] / gp, 1) if gp else 0.0,
            ppg=round(raw["PTS"] / gp, 1) if gp else 0.0,
            rpg=round(raw["REB"] / gp, 1) if gp else 0.0,
            apg=round(raw["AST"] / gp, 1) if gp else 0.0,
            spg=round(raw["STL"] / gp, 1) if gp else 0.0,
            bpg=round(raw["BLK"] / gp, 1) if gp else 0.0,
            fg_pct=raw.get("FG_PCT", 0.0),
            fg3_pct=raw.get("FG3_PCT", 0.0),
            ft_pct=raw.get("FT_PCT", 0.0),
            turnovers=round(raw["TOV"] / gp, 1) if gp else 0.0,
            plus_minus=raw.get("PLUS_MINUS", 0.0) or 0.0,
        )

        self._cache.set(cache_key, model)
        return model

    # ------------------------------------------------------------------
    # Player advanced stats
    # ------------------------------------------------------------------

    async def get_player_advanced_stats(
        self,
        player_name: str,
        season: str | None = None,
    ) -> PlayerAdvancedStats:
        """Get advanced / estimated metrics for a player in the given season."""
        player_id, name = self._resolve_player(player_name)
        season = self._season_or_current(season)
        cache_key = f"player_advanced:{player_id}:{season}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        all_rows = await self._client.get_player_estimated_metrics(season)
        row = next((r for r in all_rows if r.get("PLAYER_ID") == player_id), None)
        if row is None:
            raise ValueError(
                f"No advanced stats found for '{name}' in the {season} season."
            )

        model = PlayerAdvancedStats(
            player_name=name,
            player_id=player_id,
            season=season,
            team=row.get("TEAM_ABBREVIATION", ""),
            ts_pct=round(row.get("E_TS_PCT", 0.0), 3),
            efg_pct=round(row.get("E_EFG_PCT", 0.0), 3),
            usg_pct=round(row.get("E_USG_PCT", 0.0), 3),
            off_rating=round(row.get("E_OFF_RATING", 0.0), 1),
            def_rating=round(row.get("E_DEF_RATING", 0.0), 1),
            net_rating=round(row.get("E_NET_RATING", 0.0), 1),
            ast_ratio=round(row.get("E_AST_RATIO", 0.0), 1),
            tov_pct=round(row.get("E_TM_TOV_PCT", 0.0), 3),
            pace=round(row.get("E_PACE", 0.0), 1),
            pie=round(row.get("E_PIE", 0.0), 3),
        )

        self._cache.set(cache_key, model)
        return model

    # ------------------------------------------------------------------
    # Player recent games
    # ------------------------------------------------------------------

    async def get_player_recent_games(
        self,
        player_name: str,
        last_n: int = 10,
    ) -> list[PlayerGameLog]:
        """Return the most recent *last_n* game log entries for a player."""
        player_id, name = self._resolve_player(player_name)
        season = get_current_season()
        cache_key = f"player_games:{player_id}:{season}:{last_n}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        rows = await self._client.get_player_game_log(player_id, season, last_n)
        if not rows:
            raise ValueError(
                f"No recent games found for '{name}' in the {season} season."
            )

        games: list[PlayerGameLog] = []
        for r in rows:
            wl = r.get("WL", "")
            games.append(
                PlayerGameLog(
                    player_name=name,
                    date=r.get("GAME_DATE", ""),
                    matchup=r.get("MATCHUP", ""),
                    result=wl,
                    minutes=int(r.get("MIN", 0)),
                    points=int(r.get("PTS", 0)),
                    rebounds=int(r.get("REB", 0)),
                    assists=int(r.get("AST", 0)),
                    steals=int(r.get("STL", 0)),
                    blocks=int(r.get("BLK", 0)),
                    fg=f"{r.get('FGM', 0)}/{r.get('FGA', 0)}",
                    fg3=f"{r.get('FG3M', 0)}/{r.get('FG3A', 0)}",
                    ft=f"{r.get('FTM', 0)}/{r.get('FTA', 0)}",
                    plus_minus=r.get("PLUS_MINUS", 0.0),
                )
            )

        self._cache.set(cache_key, games)
        return games

    # ------------------------------------------------------------------
    # Player comparison
    # ------------------------------------------------------------------

    async def get_player_comparison(
        self,
        player_a: str,
        player_b: str,
    ) -> PlayerComparisonResult:
        """Compare season averages for two players side-by-side."""
        stats_a = await self.get_player_season_averages(player_a)
        stats_b = await self.get_player_season_averages(player_b)
        return PlayerComparisonResult(player_a=stats_a, player_b=stats_b)

    # ------------------------------------------------------------------
    # Team standings
    # ------------------------------------------------------------------

    async def get_team_standings(
        self,
        conference: str | None = None,
    ) -> list[TeamStanding]:
        """Return current league standings, optionally filtered by conference."""
        cache_key = f"standings:{conference or 'all'}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        rows = await self._client.get_team_standings()
        standings: list[TeamStanding] = []
        for r in rows:
            conf = r.get("Conference", "")
            standings.append(
                TeamStanding(
                    team_name=r.get("TeamName", ""),
                    team_id=int(r.get("TeamID", 0)),
                    conference=conf,
                    wins=int(r.get("WINS", 0)),
                    losses=int(r.get("LOSSES", 0)),
                    win_pct=float(r.get("WinPCT", 0.0)),
                    conference_rank=int(r.get("PlayoffRank", 0)),
                    streak=r.get("strCurrentStreak", ""),
                    last_10=r.get("L10", ""),
                )
            )

        if conference:
            conf_lower = conference.lower()
            standings = [s for s in standings if s.conference.lower() == conf_lower]

        self._cache.set(cache_key, standings)
        return standings

    async def get_team_record(self, team_name: str) -> TeamStanding:
        """Look up a single team's standing by name (substring match)."""
        all_standings = await self.get_team_standings()
        team_lower = team_name.lower()
        for standing in all_standings:
            if team_lower in standing.team_name.lower():
                return standing

        raise ValueError(
            f"Could not find a team matching '{team_name}'. "
            "Try using the full team name (e.g. 'Lakers', 'Boston Celtics')."
        )
