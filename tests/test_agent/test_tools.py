"""Tests for tool execution dispatch and TOOL_DEFINITIONS."""

import json
from unittest.mock import AsyncMock

import pytest

from legm.agent.tools import TOOL_DEFINITIONS, execute_tool
from legm.llm.types import ToolCall
from legm.stats.models import PlayerSeasonStats, TeamStanding

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def stats_service() -> AsyncMock:
    """Return an AsyncMock standing in for NBAStatsService."""
    return AsyncMock()


def _make_player_stats(**overrides) -> PlayerSeasonStats:
    """Build a PlayerSeasonStats with sensible defaults."""
    defaults = dict(
        player_name="LeBron James",
        player_id=2544,
        season="2024-25",
        team="LAL",
        games_played=50,
        mpg=35.0,
        ppg=25.0,
        rpg=7.0,
        apg=7.0,
        spg=1.2,
        bpg=0.8,
        fg_pct=0.52,
        fg3_pct=0.38,
        ft_pct=0.75,
        turnovers=3.5,
        plus_minus=4.0,
    )
    defaults.update(overrides)
    return PlayerSeasonStats(**defaults)


def _make_team_standing(**overrides) -> TeamStanding:
    """Build a TeamStanding with sensible defaults."""
    defaults = dict(
        team_name="Los Angeles Lakers",
        team_id=1610612747,
        conference="West",
        wins=35,
        losses=20,
        win_pct=0.636,
        conference_rank=4,
        streak="W3",
        last_10="7-3",
    )
    defaults.update(overrides)
    return TeamStanding(**defaults)


# ---------------------------------------------------------------------------
# TOOL_DEFINITIONS smoke test
# ---------------------------------------------------------------------------


def test_tool_definitions_is_nonempty_list() -> None:
    """TOOL_DEFINITIONS should contain at least one entry."""
    assert len(TOOL_DEFINITIONS) >= 1
    for td in TOOL_DEFINITIONS:
        assert td.name
        assert td.description
        assert "type" in td.parameters


# ---------------------------------------------------------------------------
# execute_tool — dispatch tests
# ---------------------------------------------------------------------------


async def test_execute_tool_get_player_season_averages(
    stats_service: AsyncMock,
) -> None:
    """get_player_season_averages should be dispatched and return JSON."""
    stats_service.get_player_season_averages.return_value = _make_player_stats()

    tool_call = ToolCall(
        id="tc1",
        name="get_player_season_averages",
        arguments={"player_name": "LeBron James"},
    )
    result = await execute_tool(tool_call, stats_service)

    stats_service.get_player_season_averages.assert_awaited_once_with(
        player_name="LeBron James",
        season=None,
    )
    parsed = json.loads(result)
    assert parsed["player_name"] == "LeBron James"
    assert parsed["ppg"] == 25.0


async def test_execute_tool_get_player_season_averages_with_season(
    stats_service: AsyncMock,
) -> None:
    """Season argument should be forwarded when provided."""
    stats_service.get_player_season_averages.return_value = _make_player_stats(
        season="2023-24",
    )

    tool_call = ToolCall(
        id="tc2",
        name="get_player_season_averages",
        arguments={"player_name": "LeBron James", "season": "2023-24"},
    )
    result = await execute_tool(tool_call, stats_service)

    stats_service.get_player_season_averages.assert_awaited_once_with(
        player_name="LeBron James",
        season="2023-24",
    )
    parsed = json.loads(result)
    assert parsed["season"] == "2023-24"


async def test_execute_tool_get_player_recent_games(
    stats_service: AsyncMock,
) -> None:
    """get_player_recent_games should dispatch correctly and return a JSON list."""
    from legm.stats.models import PlayerGameLog

    game = PlayerGameLog(
        player_name="LeBron James",
        date="FEB 14, 2025",
        matchup="LAL vs. BOS",
        result="W",
        minutes=36,
        points=30,
        rebounds=8,
        assists=9,
        steals=2,
        blocks=1,
        fg="12/22",
        fg3="3/7",
        ft="3/4",
        plus_minus=12.0,
    )
    stats_service.get_player_recent_games.return_value = [game]

    tool_call = ToolCall(
        id="tc3",
        name="get_player_recent_games",
        arguments={"player_name": "LeBron James", "last_n": 5},
    )
    result = await execute_tool(tool_call, stats_service)

    stats_service.get_player_recent_games.assert_awaited_once_with(
        player_name="LeBron James",
        last_n=5,
    )
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert parsed[0]["points"] == 30


async def test_execute_tool_get_team_record(
    stats_service: AsyncMock,
) -> None:
    """get_team_record should dispatch and return a single team JSON object."""
    stats_service.get_team_record.return_value = _make_team_standing()

    tool_call = ToolCall(
        id="tc4",
        name="get_team_record",
        arguments={"team_name": "Lakers"},
    )
    result = await execute_tool(tool_call, stats_service)

    stats_service.get_team_record.assert_awaited_once_with(team_name="Lakers")
    parsed = json.loads(result)
    assert parsed["team_name"] == "Los Angeles Lakers"
    assert parsed["wins"] == 35


async def test_execute_tool_get_team_standings(
    stats_service: AsyncMock,
) -> None:
    """get_team_standings should return a JSON list of standings."""
    stats_service.get_team_standings.return_value = [_make_team_standing()]

    tool_call = ToolCall(
        id="tc5",
        name="get_team_standings",
        arguments={},
    )
    result = await execute_tool(tool_call, stats_service)

    stats_service.get_team_standings.assert_awaited_once_with(conference=None)
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert len(parsed) == 1


async def test_execute_tool_get_player_comparison(
    stats_service: AsyncMock,
) -> None:
    """get_player_comparison should dispatch with both player names."""
    from legm.stats.models import PlayerComparisonResult

    comparison = PlayerComparisonResult(
        player_a=_make_player_stats(player_name="LeBron James"),
        player_b=_make_player_stats(player_name="Kevin Durant", player_id=201142),
    )
    stats_service.get_player_comparison.return_value = comparison

    tool_call = ToolCall(
        id="tc6",
        name="get_player_comparison",
        arguments={"player_a": "LeBron James", "player_b": "Kevin Durant"},
    )
    result = await execute_tool(tool_call, stats_service)

    stats_service.get_player_comparison.assert_awaited_once_with(
        player_a="LeBron James",
        player_b="Kevin Durant",
    )
    parsed = json.loads(result)
    assert parsed["player_a"]["player_name"] == "LeBron James"
    assert parsed["player_b"]["player_name"] == "Kevin Durant"


# ---------------------------------------------------------------------------
# execute_tool — error handling
# ---------------------------------------------------------------------------


async def test_execute_tool_unknown_tool_returns_error(
    stats_service: AsyncMock,
) -> None:
    """An unknown tool name should return a JSON error, not raise."""
    tool_call = ToolCall(
        id="tc_bad",
        name="nonexistent_tool",
        arguments={},
    )
    result = await execute_tool(tool_call, stats_service)

    parsed = json.loads(result)
    assert "error" in parsed
    assert "Unknown tool" in parsed["error"]


async def test_execute_tool_value_error_returns_error_json(
    stats_service: AsyncMock,
) -> None:
    """ValueError from the stats service should be caught and returned as JSON."""
    stats_service.get_player_season_averages.side_effect = ValueError(
        "Could not find an NBA player matching 'Fake Player'."
    )

    tool_call = ToolCall(
        id="tc_err",
        name="get_player_season_averages",
        arguments={"player_name": "Fake Player"},
    )
    result = await execute_tool(tool_call, stats_service)

    parsed = json.loads(result)
    assert "error" in parsed
    assert "Fake Player" in parsed["error"]
