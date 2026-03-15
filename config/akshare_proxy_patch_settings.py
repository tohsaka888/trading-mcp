from __future__ import annotations

from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    import akshare_proxy_patch
except ImportError:  # pragma: no cover
    akshare_proxy_patch: Any | None = None


_PATCH_INSTALLED = False


class AkshareProxyPatchSettings(BaseSettings):
    enabled: bool = Field(
        True,
        description="Enable akshare-proxy-patch for Eastmoney requests",
    )
    auth_ip: str | None = Field(
        None,
        description="Auth gateway IP for akshare-proxy-patch",
    )
    auth_token: str = Field(
        "",
        description="Optional auth token for akshare-proxy-patch",
    )
    retry: int = Field(
        30,
        ge=1,
        le=200,
        description="Retry count for akshare-proxy-patch",
    )

    model_config = SettingsConfigDict(
        env_prefix="TRADING_MCP_AKSHARE_PROXY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def install_akshare_proxy_patch() -> bool:
    global _PATCH_INSTALLED

    if _PATCH_INSTALLED:
        return True
    if akshare_proxy_patch is None or not hasattr(akshare_proxy_patch, "install_patch"):
        return False

    settings = AkshareProxyPatchSettings()
    if not settings.enabled or not settings.auth_ip:
        return False

    akshare_proxy_patch.install_patch(
        auth_ip=settings.auth_ip,
        auth_token=settings.auth_token,
        retry=settings.retry,
    )
    _PATCH_INSTALLED = True
    return True
