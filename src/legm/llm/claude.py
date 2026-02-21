"""Anthropic Claude provider implementation."""

import json

from anthropic import AsyncAnthropic
from anthropic.types import Message as AnthropicMessage
from anthropic.types import ToolUseBlock

from legm.llm.types import LLMResponse, Message, ToolCall, ToolDefinition


class ClaudeProvider:
    """LLM provider backed by the Anthropic Messages API."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        """Send messages to Claude and return a unified response."""
        kwargs: dict = {
            "model": self._model,
            "max_tokens": 1024,
            "messages": [_format_message(m) for m in messages],
        }
        if system is not None:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [_format_tool(t) for t in tools]

        response: AnthropicMessage = await self._client.messages.create(**kwargs)

        return _parse_response(response)


def _format_message(message: Message) -> dict:
    """Convert an internal Message to the Anthropic API format."""
    return {"role": message.role, "content": message.content}


def _format_tool(tool: ToolDefinition) -> dict:
    """Convert a ToolDefinition to the Anthropic tool schema."""
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.parameters,
    }


def _parse_response(response: AnthropicMessage) -> LLMResponse:
    """Map an Anthropic response to a unified LLMResponse."""
    text_parts: list[str] = []
    tool_calls: list[ToolCall] = []

    for block in response.content:
        if isinstance(block, ToolUseBlock):
            tool_calls.append(
                ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                    if isinstance(block.input, dict)
                    else json.loads(block.input),
                )
            )
        else:
            # TextBlock or any other block with a text attribute
            text_parts.append(block.text)

    return LLMResponse(
        content="".join(text_parts),
        tool_calls=tool_calls,
        stop_reason=response.stop_reason or "end_turn",
    )
