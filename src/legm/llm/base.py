"""Protocol definition for LLM providers."""

from typing import Protocol

from legm.llm.types import LLMResponse, Message, ToolDefinition


class LLMProvider(Protocol):
    """Async interface that all LLM backends must satisfy."""

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            messages: Conversation history.
            tools: Optional tool definitions the model may invoke.
            system: Optional system prompt prepended to the conversation.

        Returns:
            A unified LLMResponse with content, tool calls, and stop reason.
        """
        ...
