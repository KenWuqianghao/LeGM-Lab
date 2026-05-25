"""LeLM Modal web endpoint provider.

The existing ``lelm`` Modal app exposes OpenAI-shaped responses at its root
URL (``POST /``), not at ``/v1/chat/completions``.
"""

import re

import httpx

from legm.llm.types import LLMResponse, Message, ToolDefinition

_REDACTED_THINK_RE = re.compile(
    r"<think>[\s\S]*?</think>\s*", re.IGNORECASE
)


class LeLMModalProvider:
    """LLM provider for the LeLM Modal ``LeLM.chat`` root endpoint."""

    def __init__(
        self,
        base_url: str,
        model: str = "lelm",
        api_key: str = "",
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout = timeout

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        """Send messages to the Modal LeLM endpoint and return a unified response."""
        formatted: list[dict[str, str]] = []
        if system is not None:
            formatted.append({"role": "system", "content": system})
        formatted.extend(_format_message(m) for m in messages)

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "messages": formatted,
            "max_tokens": 512,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(self._base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return _parse_response(data)


def _format_message(message: Message) -> dict[str, str]:
    """Convert an internal Message to the Modal chat format."""
    if isinstance(message.content, str):
        content = message.content
    else:
        parts = [
            block.get("text", "")
            for block in message.content
            if block.get("type") == "text"
        ]
        content = "\n".join(part for part in parts if part)
    return {"role": message.role, "content": content}


def _strip_thinking(text: str) -> str:
    """Remove Qwen3 thinking blocks from model output."""
    return _REDACTED_THINK_RE.sub("", text).strip()


def _parse_response(data: dict) -> LLMResponse:
    """Map a Modal LeLM JSON response to a unified LLMResponse."""
    choice = data["choices"][0]
    message = choice.get("message", {})
    content = _strip_thinking(message.get("content", ""))
    finish_reason = choice.get("finish_reason") or "stop"
    return LLMResponse(content=content, stop_reason=finish_reason)
