"""Tool definitions and executor dispatch for the LeGM agent."""

from __future__ import annotations

import json
import logging

from legm.llm.types import ToolCall, ToolDefinition
from legm.stats.service import NBAStatsService

logger = logging.getLogger(__name__)

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
    ToolDefinition(
        name="web_search",
        description=(
            "Search the web for NBA information. Use this FIRST when you "
            "encounter unknown player acronyms/nicknames (e.g. 'DFS', 'PG13', "
            "'The Brow'), recent trades/signings, or anything the stats tools "
            "can't answer. Returns text snippets from top results."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search query. Be specific, e.g. "
                        "'DFS NBA player full name' or "
                        "'NBA trade deadline 2025 results'"
                    ),
                },
            },
            "required": ["query"],
        },
    ),
]


async def _exa_search(query: str, api_key: str) -> str:
    """Run an Exa web search and return condensed text snippets."""
    from exa_py import AsyncExa

    exa = AsyncExa(api_key=api_key)
    results = await exa.search(
        query,
        num_results=3,
        contents={"text": {"max_characters": 500}},
    )
    snippets = []
    for r in results.results:
        snippets.append(f"[{r.title}] {r.text}")
    return "\n---\n".join(snippets) if snippets else "No results found."


async def execute_tool(
    tool_call: ToolCall,
    stats_service: NBAStatsService,
    exa_api_key: str = "",
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
        elif name == "web_search":
            if not exa_api_key:
                return json.dumps({"error": "EXA_API_KEY not configured"})
            return await _exa_search(args["query"], exa_api_key)
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        logger.exception("Tool %s failed", name)
        return json.dumps({"error": f"Tool error: {exc}"})

    if isinstance(result, list):
        return json.dumps(
            [r.model_dump() for r in result],
            default=str,
        )
    return json.dumps(result.model_dump(), default=str)
