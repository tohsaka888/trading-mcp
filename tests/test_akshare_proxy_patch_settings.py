from __future__ import annotations

from config import akshare_proxy_patch_settings


def test_install_akshare_proxy_patch_noops_without_auth_ip(monkeypatch) -> None:
    monkeypatch.delenv("TRADING_MCP_AKSHARE_PROXY_AUTH_IP", raising=False)
    monkeypatch.setattr(akshare_proxy_patch_settings, "_PATCH_INSTALLED", False)
    monkeypatch.setattr(
        akshare_proxy_patch_settings,
        "akshare_proxy_patch",
        object(),
    )

    assert akshare_proxy_patch_settings.install_akshare_proxy_patch() is False


def test_install_akshare_proxy_patch_uses_env_settings(monkeypatch) -> None:
    calls: dict[str, object] = {}

    class FakePatch:
        @staticmethod
        def install_patch(*, auth_ip: str, auth_token: str, retry: int) -> None:
            calls["auth_ip"] = auth_ip
            calls["auth_token"] = auth_token
            calls["retry"] = retry

    monkeypatch.setenv("TRADING_MCP_AKSHARE_PROXY_AUTH_IP", "10.0.0.8")
    monkeypatch.setenv("TRADING_MCP_AKSHARE_PROXY_AUTH_TOKEN", "token-1")
    monkeypatch.setenv("TRADING_MCP_AKSHARE_PROXY_RETRY", "15")
    monkeypatch.setattr(akshare_proxy_patch_settings, "_PATCH_INSTALLED", False)
    monkeypatch.setattr(
        akshare_proxy_patch_settings,
        "akshare_proxy_patch",
        FakePatch(),
    )

    assert akshare_proxy_patch_settings.install_akshare_proxy_patch() is True
    assert calls == {
        "auth_ip": "10.0.0.8",
        "auth_token": "token-1",
        "retry": 15,
    }


def test_install_akshare_proxy_patch_is_idempotent(monkeypatch) -> None:
    calls = {"count": 0}

    class FakePatch:
        @staticmethod
        def install_patch(*, auth_ip: str, auth_token: str, retry: int) -> None:
            calls["count"] += 1

    monkeypatch.setenv("TRADING_MCP_AKSHARE_PROXY_AUTH_IP", "10.0.0.8")
    monkeypatch.setattr(akshare_proxy_patch_settings, "_PATCH_INSTALLED", False)
    monkeypatch.setattr(
        akshare_proxy_patch_settings,
        "akshare_proxy_patch",
        FakePatch(),
    )

    assert akshare_proxy_patch_settings.install_akshare_proxy_patch() is True
    assert akshare_proxy_patch_settings.install_akshare_proxy_patch() is True
    assert calls["count"] == 1
