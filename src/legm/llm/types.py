"""Data classes for the LLM abstraction layer."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Message:
    """A single message in a conversation."""

    role: str
    content: str | list[dict]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Schema for a tool the LLM can invoke."""

    name: str
    description: str
    parameters: dict  # JSON Schema object


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A tool invocation returned by the LLM."""

    id: str
    name: str
    arguments: dict


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Unified response from any LLM provider."""

    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"
