"""Tool definitions and executor dispatch for the LeGM agent."""

import json

from legm.llm.types import ToolCall, ToolDefinition
from legm.stats.service import NBAStatsService

TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="get_player_season_averages",
        description=(
            "Get a player's per-game averages for a given season. "
            "Returns points, rebounds, assists, shooting percentages, etc."
        ),
        parameters={
            "type": "object",
            "properties": {
                "player_name": {
                    "type": "string",
                    "description": "Full name of the NBA player (e.g. 'LeBron James')",
                },
                "season": {
                    "type": "string",
                    "description": "Season string like '2024-25'. Omit for current.",
                },
            },
            "required": ["player_name"],
        },
    ),
    ToolDefinition(
        name="get_player_recent_games",
        description=(
            "Get a player's most recent game logs. "
            "Returns date, matchup, points, rebounds, assists, etc. for each game."
        ),
        parameters={
            "type": "object",
            "properties": {
                "player_name": {
                    "type": "string",
                    "description": "Full name of the NBA player",
                },
                "last_n": {
                    "type": "integer",
                    "description": "Number of recent games to fetch (default 10)",
                },
            },
            "required": ["player_name"],
        },
    ),
    ToolDefinition(
        name="get_player_comparison",
        description=(
            "Compare two players' season averages side-by-side. "
            "Useful for 'Player A vs Player B' takes."
        ),
        parameters={
            "type": "object",
            "properties": {
                "player_a": {
                    "type": "string",
                    "description": "Full name of the first player",
                },
                "player_b": {
                    "type": "string",
                    "description": "Full name of the second player",
                },
            },
            "required": ["player_a", "player_b"],
        },
    ),
    ToolDefinition(
        name="get_player_advanced_stats",
        description=(
            "Get a player's advanced metrics: true shooting % (TS%), "
            "usage rate, offensive/defensive/net rating, assist ratio, "
            "turnover %, pace, and PIE. Use TS% over FG% for shooting "
            "arguments, net rating for impact, usage for volume."
        ),
        parameters={
            "type": "object",
            "properties": {
                "player_name": {
                    "type": "string",
                    "description": "Full name of the NBA player (e.g. 'LeBron James')",
                },
                "season": {
                    "type": "string",
                    "description": "Season string like '2024-25'. Omit for current.",
                },
            },
            "required": ["player_name"],
        },
    ),
    ToolDefinition(
        name="get_team_standings",
        description=(
            "Get current NBA standings. Optionally filter by conference. "
            "Returns wins, losses, win%, rank, streak."
        ),
        parameters={
            "type": "object",
            "properties": {
                "conference": {
                    "type": "string",
                    "description": "Filter by 'East' or 'West'. Omit for both.",
                },
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_team_record",
        description=(
            "Get a single team's record and standing. "
            "Use substring matching (e.g. 'Lakers', 'Celtics')."
        ),
        parameters={
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "Team name or partial name (e.g. 'Lakers')",
                },
            },
            "required": ["team_name"],
        },
    ),
]


async def execute_tool(
    tool_call: ToolCall,
    stats_service: NBAStatsService,
) -> str:
    """Execute a tool call and return the JSON-serialized result."""
    name = tool_call.name
    args = tool_call.arguments

    try:
        if name == "get_player_season_averages":
            result = await stats_service.get_player_season_averages(
                player_name=args["player_name"],
                season=args.get("season"),
            )
        elif name == "get_player_recent_games":
            result = await stats_service.get_player_recent_games(
                player_name=args["player_name"],
                last_n=args.get("last_n", 10),
            )
        elif name == "get_player_advanced_stats":
            result = await stats_service.get_player_advanced_stats(
                player_name=args["player_name"],
                season=args.get("season"),
            )
        elif name == "get_player_comparison":
            result = await stats_service.get_player_comparison(
                player_a=args["player_a"],
                player_b=args["player_b"],
            )
        elif name == "get_team_standings":
            result = await stats_service.get_team_standings(
                conference=args.get("conference"),
            )
        elif name == "get_team_record":
            result = await stats_service.get_team_record(
                team_name=args["team_name"],
            )
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        return json.dumps({"error": f"Stats API error: {exc}"})

    if isinstance(result, list):
        return json.dumps(
            [r.model_dump() for r in result],
            default=str,
        )
    return json.dumps(result.model_dump(), default=str)
