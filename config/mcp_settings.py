from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class McpServerSettings(BaseSettings):
    host: str = Field("0.0.0.0", description="Host interface for MCP server")
    port: int = Field(8000, ge=1, le=65535, description="Port for MCP server")

    model_config = SettingsConfigDict(
        env_prefix="TRADING_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
