"""Factory for constructing the configured LLM provider."""

from legm.config import LLMProvider as LLMProviderEnum
from legm.config import Settings
from legm.llm.base import LLMProvider
from legm.llm.claude import ClaudeProvider
from legm.llm.lelm_modal import LeLMModalProvider
from legm.llm.openai_compat import OpenAICompatProvider

_LELM_MODAL_HOST = "lelm-lelm-chat.modal.run"


def _lelm_modal_base_url(base_url: str) -> str | None:
    """Return the root Modal URL when *base_url* targets the LeLM chat endpoint."""
    normalized = base_url.rstrip("/")
    if _LELM_MODAL_HOST not in normalized:
        return None
    return normalized.removesuffix("/v1")


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Instantiate the LLM provider specified in *settings*.

    Args:
        settings: Application settings containing provider choice and credentials.

    Returns:
        An LLMProvider implementation ready for use.

    Raises:
        ValueError: If the configured provider is not recognised.
    """
    match settings.llm_provider:
        case LLMProviderEnum.CLAUDE:
            return ClaudeProvider(
                api_key=settings.anthropic_api_key,
                model=settings.llm_model,
            )
        case LLMProviderEnum.OPENAI:
            return OpenAICompatProvider(
                api_key=settings.openai_api_key,
                model=settings.llm_model,
            )
        case LLMProviderEnum.OPENAI_COMPAT:
            lelm_base = _lelm_modal_base_url(settings.openai_compat_base_url)
            if lelm_base is not None:
                return LeLMModalProvider(
                    api_key=settings.openai_compat_api_key,
                    model=settings.openai_compat_model or settings.llm_model,
                    base_url=lelm_base,
                )
            return OpenAICompatProvider(
                api_key=settings.openai_compat_api_key,
                model=settings.openai_compat_model or settings.llm_model,
                base_url=settings.openai_compat_base_url or None,
            )
        case _:
            raise ValueError(f"Unknown LLM provider: {settings.llm_provider!r}")
