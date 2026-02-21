"""Tests for the LLM provider factory."""

from unittest.mock import patch

import pytest

from legm.config import LLMProvider as LLMProviderEnum
from legm.config import Settings
from legm.llm.claude import ClaudeProvider
from legm.llm.factory import create_llm_provider
from legm.llm.openai_compat import OpenAICompatProvider


class TestCreateLLMProvider:
    """Tests for ``create_llm_provider``."""

    @patch("legm.llm.claude.AsyncAnthropic")
    def test_claude_provider(
        self, _mock_anthropic: object, test_settings: Settings
    ) -> None:
        """Factory returns a ClaudeProvider when configured for Claude."""
        test_settings = test_settings.model_copy(
            update={"llm_provider": LLMProviderEnum.CLAUDE}
        )
        provider = create_llm_provider(test_settings)
        assert isinstance(provider, ClaudeProvider)

    @patch("legm.llm.openai_compat.AsyncOpenAI")
    def test_openai_provider(
        self, _mock_openai: object, test_settings: Settings
    ) -> None:
        """Factory returns an OpenAICompatProvider when configured for OpenAI."""
        test_settings = test_settings.model_copy(
            update={"llm_provider": LLMProviderEnum.OPENAI}
        )
        provider = create_llm_provider(test_settings)
        assert isinstance(provider, OpenAICompatProvider)

    @patch("legm.llm.openai_compat.AsyncOpenAI")
    def test_openai_compat_provider(
        self, _mock_openai: object, test_settings: Settings
    ) -> None:
        """Factory returns an OpenAICompatProvider when configured for openai_compat."""
        test_settings = test_settings.model_copy(
            update={"llm_provider": LLMProviderEnum.OPENAI_COMPAT}
        )
        provider = create_llm_provider(test_settings)
        assert isinstance(provider, OpenAICompatProvider)

    def test_unknown_provider_raises(self, test_settings: Settings) -> None:
        """Factory raises ValueError for an unrecognised provider string."""
        # Force an invalid provider value by bypassing Pydantic validation
        object.__setattr__(test_settings, "llm_provider", "not_a_real_provider")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_provider(test_settings)
