"""Tests for TakeAnalyzer — the core agent loop and response parsing."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from legm.agent.analyzer import TakeAnalysis, TakeAnalyzer, _parse_analysis
from legm.llm.types import LLMResponse, ToolCall
from legm.stats.models import ChartData
from legm.stats.service import NBAStatsService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_stats_service() -> AsyncMock:
    """Return an AsyncMock that stands in for NBAStatsService."""
    svc = AsyncMock(spec=NBAStatsService)
    return svc


@pytest.fixture()
def mock_llm() -> AsyncMock:
    """Return an AsyncMock LLM provider."""
    return AsyncMock()


FINAL_JSON = json.dumps(
    {
        "verdict": "trash",
        "confidence": 0.9,
        "roast": (
            "Bro said LeBron is washed? He averaging 25/7/7 dawg "
            "respectfully delete this"
        ),
        "reasoning": "LeBron still elite",
        "stats_used": ["25.0 PPG"],
    }
)


# ---------------------------------------------------------------------------
# TakeAnalyzer.analyze — happy-path with tool calls then final JSON
# ---------------------------------------------------------------------------


async def test_analyze_calls_llm_and_handles_tool_calls(
    mock_llm: AsyncMock,
    mock_stats_service: AsyncMock,
) -> None:
    """analyze() should call the LLM, execute tool calls, then return TakeAnalysis."""
    tool_call = ToolCall(
        id="1",
        name="get_player_season_averages",
        arguments={"player_name": "LeBron James"},
    )

    # Round 1 → LLM asks for a tool call
    round_1_response = LLMResponse(
        content="",
        tool_calls=[tool_call],
    )
    # Round 2 → LLM returns final JSON
    round_2_response = LLMResponse(content=FINAL_JSON)

    mock_llm.generate = AsyncMock(
        side_effect=[round_1_response, round_2_response],
    )

    # Mock execute_tool indirectly via stats service returning a model
    mock_stats_service.get_player_season_averages.return_value = MagicMock(
        model_dump=lambda: {
            "player_name": "LeBron James",
            "ppg": 25.0,
            "rpg": 7.0,
            "apg": 7.0,
        },
    )

    analyzer = TakeAnalyzer(llm=mock_llm, stats_service=mock_stats_service)
    result = await analyzer.analyze("LeBron is washed")

    assert isinstance(result, TakeAnalysis)
    assert result.verdict == "trash"
    assert result.confidence == 0.9
    assert "25/7/7" in result.roast
    assert result.stats_used == ["25.0 PPG"]

    # LLM was called twice (tool round + final)
    assert mock_llm.generate.call_count == 2


async def test_analyze_no_tool_calls_returns_immediately(
    mock_llm: AsyncMock,
    mock_stats_service: AsyncMock,
) -> None:
    """When the LLM returns no tool_calls on the first round, parse immediately."""
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(content=FINAL_JSON),
    )

    analyzer = TakeAnalyzer(llm=mock_llm, stats_service=mock_stats_service)
    result = await analyzer.analyze("LeBron is the GOAT")

    assert isinstance(result, TakeAnalysis)
    assert result.verdict == "trash"
    assert mock_llm.generate.call_count == 1
    # Stats service should not have been called
    mock_stats_service.get_player_season_averages.assert_not_awaited()


# ---------------------------------------------------------------------------
# _parse_analysis — unit tests for the JSON parser
# ---------------------------------------------------------------------------


class TestParseAnalysis:
    """Tests for the _parse_analysis helper function."""

    def test_valid_json(self) -> None:
        """Plain JSON string should be parsed correctly."""
        result = _parse_analysis(FINAL_JSON)

        assert result.verdict == "trash"
        assert result.confidence == 0.9
        assert "delete this" in result.roast
        assert result.reasoning == "LeBron still elite"
        assert result.stats_used == ["25.0 PPG"]

    def test_markdown_wrapped_json(self) -> None:
        """JSON wrapped in ```json ... ``` fences should be parsed correctly."""
        wrapped = f"```json\n{FINAL_JSON}\n```"
        result = _parse_analysis(wrapped)

        assert result.verdict == "trash"
        assert result.confidence == 0.9

    def test_markdown_wrapped_no_lang_tag(self) -> None:
        """JSON wrapped in bare ``` fences (no language tag) should also work."""
        wrapped = f"```\n{FINAL_JSON}\n```"
        result = _parse_analysis(wrapped)

        assert result.verdict == "trash"

    def test_invalid_json_returns_fallback(self) -> None:
        """Non-JSON content should return a fallback TakeAnalysis with 'mid' verdict."""
        result = _parse_analysis("this is not json at all")

        assert result.verdict == "mid"
        assert result.confidence == 0.5
        assert "this is not json at all" in result.roast
        assert "Failed to parse" in result.reasoning
        assert result.stats_used == []

    def test_empty_string_returns_fallback(self) -> None:
        """Empty content should return a fallback with a default roast."""
        result = _parse_analysis("")

        assert result.verdict == "mid"
        assert result.confidence == 0.5
        assert result.roast == "Couldn't process this take dawg"

    def test_missing_fields_use_defaults(self) -> None:
        """JSON with missing optional fields should use sensible defaults."""
        partial = json.dumps({"verdict": "valid", "roast": "Solid take"})
        result = _parse_analysis(partial)

        assert result.verdict == "valid"
        assert result.confidence == 0.5  # default
        assert result.roast == "Solid take"
        assert result.reasoning == ""  # default
        assert result.stats_used == []  # default

    def test_roast_truncated_to_280_chars(self) -> None:
        """Roast should be truncated to 280 characters (tweet length)."""
        long_roast = "A" * 500
        data = json.dumps({"verdict": "trash", "roast": long_roast})
        result = _parse_analysis(data)

        assert len(result.roast) == 280


# ---------------------------------------------------------------------------
# chart_data parsing and rendering tests
# ---------------------------------------------------------------------------

CHART_DATA_JSON = {
    "title": "2016 NBA Finals — Games 5-7",
    "subtitle": "When it mattered most",
    "label_a": "LeBron James",
    "label_b": "Stephen Curry",
    "rows": [
        {"label": "PPG", "value_a": 36.3, "value_b": 22.4, "fmt": "number", "higher_is_better": True},
        {"label": "FG%", "value_a": 0.487, "value_b": 0.403, "fmt": "percent", "higher_is_better": True},
    ],
}


class TestChartDataParsing:
    """Tests for chart_data extraction in _parse_analysis."""

    def test_parse_analysis_with_chart_data(self) -> None:
        """Valid chart_data in JSON should produce a ChartData instance."""
        data = json.dumps({
            "verdict": "trash",
            "confidence": 0.92,
            "roast": "LeBron cooked",
            "reasoning": "Finals dominance",
            "stats_used": ["36.3 PPG"],
            "chart_data": CHART_DATA_JSON,
        })
        result = _parse_analysis(data)

        assert isinstance(result.chart_data, ChartData)
        assert result.chart_data.title == "2016 NBA Finals — Games 5-7"
        assert result.chart_data.label_a == "LeBron James"
        assert result.chart_data.label_b == "Stephen Curry"
        assert len(result.chart_data.rows) == 2
        assert result.chart_data.rows[0].label == "PPG"
        assert result.chart_data.rows[0].value_a == 36.3

    def test_parse_analysis_invalid_chart_data_falls_back(self) -> None:
        """Malformed chart_data should fall back to None, not crash."""
        data = json.dumps({
            "verdict": "trash",
            "roast": "bad chart",
            "chart_data": {"title": "Missing required fields"},
        })
        result = _parse_analysis(data)

        assert result.chart_data is None
        assert result.verdict == "trash"


async def test_analyze_generates_chart_png_from_chart_data(
    mock_llm: AsyncMock,
    mock_stats_service: AsyncMock,
) -> None:
    """When LLM returns chart_data, analyze() should produce chart_png bytes."""
    response_with_chart = json.dumps({
        "verdict": "trash",
        "confidence": 0.9,
        "roast": "cooked",
        "reasoning": "numbers",
        "stats_used": [],
        "chart_data": CHART_DATA_JSON,
    })

    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(content=response_with_chart),
    )

    fake_png = b"fake-png-bytes"
    with patch("legm.agent.analyzer.generate_flexible_chart", return_value=fake_png) as mock_chart:
        analyzer = TakeAnalyzer(llm=mock_llm, stats_service=mock_stats_service)
        result = await analyzer.analyze("some take")

    assert result.chart_png == fake_png
    assert result.chart_data is not None
    mock_chart.assert_called_once()


async def test_analyze_no_chart_when_chart_data_absent(
    mock_llm: AsyncMock,
    mock_stats_service: AsyncMock,
) -> None:
    """When LLM returns no chart_data, chart_png should be None."""
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(content=FINAL_JSON),
    )

    analyzer = TakeAnalyzer(llm=mock_llm, stats_service=mock_stats_service)
    result = await analyzer.analyze("LeBron is the GOAT")

    assert result.chart_data is None
    assert result.chart_png is None
