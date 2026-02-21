"""Pydantic v2 models for NBA stats data."""

from pydantic import BaseModel, Field


class PlayerSeasonStats(BaseModel):
    """Aggregated season averages for an NBA player."""

    player_name: str
    player_id: int
    season: str = Field(description="Season string, e.g. '2024-25'")
    team: str
    games_played: int
    mpg: float = Field(description="Minutes per game")
    ppg: float = Field(description="Points per game")
    rpg: float = Field(description="Rebounds per game")
    apg: float = Field(description="Assists per game")
    spg: float = Field(description="Steals per game")
    bpg: float = Field(description="Blocks per game")
    fg_pct: float = Field(description="Field goal percentage (0.0–1.0)")
    fg3_pct: float = Field(description="Three-point percentage (0.0–1.0)")
    ft_pct: float = Field(description="Free throw percentage (0.0–1.0)")
    turnovers: float = Field(description="Turnovers per game")
    plus_minus: float


class PlayerGameLog(BaseModel):
    """A single game entry from a player's game log."""

    player_name: str
    date: str = Field(description="Game date, e.g. 'FEB 14, 2025'")
    matchup: str = Field(description="Matchup string, e.g. 'LAL vs. BOS'")
    result: str = Field(description="W or L")
    minutes: int
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    fg: str = Field(description="Field goals made/attempted, e.g. '10/20'")
    fg3: str = Field(description="Three-pointers made/attempted, e.g. '3/7'")
    ft: str = Field(description="Free throws made/attempted, e.g. '5/6'")
    plus_minus: float


class TeamStanding(BaseModel):
    """Conference standings entry for an NBA team."""

    team_name: str
    team_id: int
    conference: str = Field(description="'East' or 'West'")
    wins: int
    losses: int
    win_pct: float
    conference_rank: int
    streak: str = Field(description="Current streak, e.g. 'W3' or 'L2'")
    last_10: str = Field(description="Record over last 10 games, e.g. '7-3'")


class PlayerAdvancedStats(BaseModel):
    """Advanced / estimated metrics for an NBA player."""

    player_name: str
    player_id: int
    season: str = Field(description="Season string, e.g. '2024-25'")
    team: str
    ts_pct: float = Field(description="True shooting percentage")
    efg_pct: float = Field(description="Effective field goal percentage")
    usg_pct: float = Field(description="Usage rate")
    off_rating: float = Field(description="Offensive rating (pts per 100 poss)")
    def_rating: float = Field(description="Defensive rating (pts allowed per 100 poss)")
    net_rating: float = Field(description="Net rating (off - def)")
    ast_ratio: float = Field(description="Assist ratio")
    tov_pct: float = Field(description="Turnover percentage")
    pace: float = Field(description="Pace (possessions per 48 min)")
    pie: float = Field(description="Player Impact Estimate")


class PlayerComparisonResult(BaseModel):
    """Side-by-side comparison of two players' season stats."""

    player_a: PlayerSeasonStats
    player_b: PlayerSeasonStats


class ChartRow(BaseModel):
    """A single row in a flexible chart."""

    label: str = Field(description="Stat label, e.g. 'PPG', 'FG%', 'FTs Awarded'")
    value_a: float = Field(description="Primary entity value")
    value_b: float | None = Field(
        default=None, description="Second entity value (None for single-entity charts)"
    )
    fmt: str = Field(
        default="number",
        description="Format hint: 'number' (12.3), 'percent' (52.1%), 'plus' (+4.2)",
    )
    higher_is_better: bool = Field(
        default=True, description="Whether higher values are better for this stat"
    )


class ChartData(BaseModel):
    """Agent-provided chart specification — the LLM decides what gets visualized."""

    title: str = Field(description="Chart title, e.g. '2016 NBA Finals — Games 5-7'")
    subtitle: str | None = Field(
        default=None, description="Optional subtitle for extra context"
    )
    label_a: str = Field(description="Primary entity label, e.g. 'LeBron James'")
    label_b: str | None = Field(
        default=None,
        description="Second entity label (None for single-entity charts)",
    )
    rows: list[ChartRow] = Field(
        description="4-7 stat rows to display", min_length=1, max_length=10
    )
