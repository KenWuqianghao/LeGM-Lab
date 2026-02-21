"""LLM abstraction layer — provider-agnostic interface for language models."""

from legm.llm.base import LLMProvider
from legm.llm.claude import ClaudeProvider
from legm.llm.factory import create_llm_provider
from legm.llm.openai_compat import OpenAICompatProvider
from legm.llm.types import LLMResponse, Message, ToolCall, ToolDefinition

__all__ = [
    "ClaudeProvider",
    "LLMProvider",
    "LLMResponse",
    "Message",
    "OpenAICompatProvider",
    "ToolCall",
    "ToolDefinition",
    "create_llm_provider",
]
