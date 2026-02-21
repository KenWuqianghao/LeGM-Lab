"""Tests for the LLM type dataclasses."""

from dataclasses import FrozenInstanceError

import pytest

from legm.llm.types import LLMResponse, Message, ToolCall, ToolDefinition

# ------------------------------------------------------------------
# Message
# ------------------------------------------------------------------


class TestMessage:
    """Tests for the Message dataclass."""

    def test_instantiation(self) -> None:
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_content_can_be_list(self) -> None:
        blocks = [{"type": "text", "text": "hi"}]
        msg = Message(role="assistant", content=blocks)
        assert msg.content == blocks

    def test_frozen(self) -> None:
        msg = Message(role="user", content="hello")
        with pytest.raises(FrozenInstanceError):
            msg.role = "assistant"  # type: ignore[misc]

    def test_slots(self) -> None:
        msg = Message(role="user", content="hello")
        assert not hasattr(msg, "__dict__")


# ------------------------------------------------------------------
# ToolCall
# ------------------------------------------------------------------


class TestToolCall:
    """Tests for the ToolCall dataclass."""

    def test_instantiation(self) -> None:
        tc = ToolCall(id="tc_1", name="get_stats", arguments={"player": "LeBron"})
        assert tc.id == "tc_1"
        assert tc.name == "get_stats"
        assert tc.arguments == {"player": "LeBron"}

    def test_frozen(self) -> None:
        tc = ToolCall(id="tc_1", name="get_stats", arguments={})
        with pytest.raises(FrozenInstanceError):
            tc.name = "other"  # type: ignore[misc]

    def test_slots(self) -> None:
        tc = ToolCall(id="tc_1", name="get_stats", arguments={})
        assert not hasattr(tc, "__dict__")


# ------------------------------------------------------------------
# ToolDefinition
# ------------------------------------------------------------------


class TestToolDefinition:
    """Tests for the ToolDefinition dataclass."""

    def test_instantiation(self) -> None:
        td = ToolDefinition(
            name="search",
            description="Search for players",
            parameters={"type": "object", "properties": {}},
        )
        assert td.name == "search"
        assert td.description == "Search for players"
        assert td.parameters == {"type": "object", "properties": {}}

    def test_frozen(self) -> None:
        td = ToolDefinition(name="search", description="desc", parameters={})
        with pytest.raises(FrozenInstanceError):
            td.description = "new"  # type: ignore[misc]

    def test_slots(self) -> None:
        td = ToolDefinition(name="search", description="desc", parameters={})
        assert not hasattr(td, "__dict__")


# ------------------------------------------------------------------
# LLMResponse
# ------------------------------------------------------------------


class TestLLMResponse:
    """Tests for the LLMResponse dataclass."""

    def test_instantiation_with_defaults(self) -> None:
        resp = LLMResponse(content="Hello!")
        assert resp.content == "Hello!"
        assert resp.tool_calls == []
        assert resp.stop_reason == "end_turn"

    def test_instantiation_with_all_fields(self) -> None:
        tc = ToolCall(id="tc_1", name="fn", arguments={})
        resp = LLMResponse(
            content="text",
            tool_calls=[tc],
            stop_reason="tool_use",
        )
        assert resp.content == "text"
        assert resp.tool_calls == [tc]
        assert resp.stop_reason == "tool_use"

    def test_frozen(self) -> None:
        resp = LLMResponse(content="hi")
        with pytest.raises(FrozenInstanceError):
            resp.content = "bye"  # type: ignore[misc]

    def test_slots(self) -> None:
        resp = LLMResponse(content="hi")
        assert not hasattr(resp, "__dict__")

    def test_default_tool_calls_are_independent(self) -> None:
        """Each instance should get its own empty list for tool_calls."""
        a = LLMResponse(content="a")
        b = LLMResponse(content="b")
        assert a.tool_calls is not b.tool_calls
