"""OpenAI-compatible provider implementation.

Works with the official OpenAI API as well as any provider exposing the same
chat-completions interface (DeepSeek, Together, Groq, local vLLM, etc.).
"""

import json

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from legm.llm.types import LLMResponse, Message, ToolCall, ToolDefinition


class OpenAICompatProvider:
    """LLM provider for OpenAI and OpenAI-compatible endpoints."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
    ) -> None:
        client_kwargs: dict = {"api_key": api_key}
        if base_url is not None:
            client_kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**client_kwargs)
        self._model = model

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        """Send messages via the chat completions API and return a unified response."""
        formatted: list[dict] = []
        if system is not None:
            formatted.append({"role": "system", "content": system})
        formatted.extend(_format_message(m) for m in messages)

        kwargs: dict = {
            "model": self._model,
            "messages": formatted,
        }
        if tools:
            kwargs["tools"] = [_format_tool(t) for t in tools]

        response: ChatCompletion = await self._client.chat.completions.create(**kwargs)

        return _parse_response(response)


def _format_message(message: Message) -> dict:
    """Convert an internal Message to the OpenAI chat format."""
    return {"role": message.role, "content": message.content}


def _format_tool(tool: ToolDefinition) -> dict:
    """Convert a ToolDefinition to an OpenAI function-calling tool schema."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


def _parse_response(response: ChatCompletion) -> LLMResponse:
    """Map an OpenAI chat completion to a unified LLMResponse."""
    choice = response.choices[0]
    message = choice.message

    content = message.content or ""
    tool_calls: list[ToolCall] = []

    if message.tool_calls:
        for tc in message.tool_calls:
            tool_calls.append(
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                )
            )

    # Map OpenAI finish reasons to our stop_reason vocabulary
    stop_reason = "tool_use" if tool_calls else (choice.finish_reason or "end_turn")

    return LLMResponse(
        content=content,
        tool_calls=tool_calls,
        stop_reason=stop_reason,
    )
