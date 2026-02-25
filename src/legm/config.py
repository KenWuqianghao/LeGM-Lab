"""Environment-driven configuration using Pydantic Settings."""

import os
from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings

_DEFAULT_DB_URL = (
    "sqlite+aiosqlite:////data/legm.db"
    if os.path.isdir("/data")
    else "sqlite+aiosqlite:///./legm.db"
)


class LLMProvider(StrEnum):
    CLAUDE = "claude"
    OPENAI = "openai"
    OPENAI_COMPAT = "openai_compat"


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # LLM
    llm_provider: LLMProvider = LLMProvider.CLAUDE
    llm_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openai_compat_base_url: str = ""
    openai_compat_api_key: str = ""

    # Database
    database_url: str = _DEFAULT_DB_URL

    # Twitter/X
    twitter_bearer_token: str = ""
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    twitter_access_token: str = ""
    twitter_access_token_secret: str = ""
    twitter_bot_user_id: str = ""
    twitter_bot_username: str = ""

    # Bot
    bot_mention_poll_interval: int = Field(
        default=60, description="Seconds between mention polls"
    )
    bot_search_poll_interval: int = Field(
        default=300, description="Seconds between search polls"
    )
    bot_max_daily_proactive: int = Field(
        default=20, description="Max proactive tweets per day"
    )
    bot_monthly_budget: int = Field(default=450, description="Monthly tweet budget")
    bot_dry_run: bool = Field(default=False, description="Log actions without posting")
    bot_proactive_enabled: bool = Field(
        default=False, description="Enable proactive tweet searching"
    )


settings = Settings()
