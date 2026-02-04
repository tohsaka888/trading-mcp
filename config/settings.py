from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings validated via pydantic."""

    environment: str = Field(..., description="Runtime environment, e.g. dev/test/prod")
    data_dir: Path = Field(..., description="Base directory for local data")
    default_symbol: str = Field(..., description="Default market symbol")

    model_config = SettingsConfigDict(
        env_prefix="TRADING_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def load_settings(**overrides: object) -> Settings:
    """Load settings with optional overrides (env vars still apply)."""

    return Settings(**overrides)
