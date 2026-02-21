"""Player name resolution and season utilities."""

from datetime import datetime

from nba_api.stats.static import players as nba_players


def normalize_name(name: str) -> str:
    """Lowercase, strip whitespace, and collapse multiple spaces."""
    return " ".join(name.lower().split())


def find_player_id(name: str) -> int | None:
    """Resolve a human-typed player name to an nba_api player ID.

    Tries three strategies in order:
    1. Exact / full-name search via ``find_players_by_full_name``.
    2. Partial match on the full player list.
    3. Split into first / last and search each independently.

    Returns the player ID of the best match, or ``None`` if nothing
    was found.
    """
    if not name or not name.strip():
        return None

    normalized = normalize_name(name)

    # Strategy 1 — full name search (nba_api does case-insensitive substring)
    matches = nba_players.find_players_by_full_name(normalized)
    if matches:
        # Prefer an active player when multiple results come back
        active = [m for m in matches if m.get("is_active")]
        best = active[0] if active else matches[0]
        return int(best["id"])

    # Strategy 2 — iterate all players for a loose substring match
    all_players = nba_players.get_players()
    partial = [p for p in all_players if normalized in normalize_name(p["full_name"])]
    if partial:
        active = [p for p in partial if p.get("is_active")]
        best = active[0] if active else partial[0]
        return int(best["id"])

    # Strategy 3 — try first name and last name separately
    parts = normalized.split()
    if len(parts) >= 2:
        first, last = parts[0], parts[-1]
        by_last = nba_players.find_players_by_last_name(last)
        for player in by_last:
            if first in normalize_name(player["first_name"]):
                return int(player["id"])

    return None


def get_current_season() -> str:
    """Return the current NBA season string (e.g. ``'2024-25'``).

    The NBA season straddles two calendar years. If the current month is
    October or later the season started this year; otherwise it started
    last year.
    """
    today = datetime.now()  # noqa: DTZ005
    start_year = today.year if today.month >= 10 else today.year - 1
    end_year_short = str(start_year + 1)[-2:]
    return f"{start_year}-{end_year_short}"
