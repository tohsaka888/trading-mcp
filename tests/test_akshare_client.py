from __future__ import annotations

import pandas as pd

from data import akshare_client


def test_fetch_falls_back_to_tencent_with_normalized_symbol(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_hist(*, symbol: str, start_date: str, end_date: str, adjust: str):
        calls["hist"] = symbol
        return pd.DataFrame()

    def fake_hist_tx(*, symbol: str, start_date: str, end_date: str, adjust: str):
        calls["hist_tx"] = symbol
        return pd.DataFrame(
            {
                "date": ["2024-01-01"],
                "open": [1.0],
                "high": [1.0],
                "low": [1.0],
                "close": [1.0],
            }
        )

    monkeypatch.setattr(akshare_client.ak, "stock_zh_a_hist", fake_hist)
    monkeypatch.setattr(akshare_client.ak, "stock_zh_a_hist_tx", fake_hist_tx)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch("300308.SZ", "2024-01-01", "2024-01-10")

    assert calls["hist"] == "300308"
    assert calls["hist_tx"] == "sz300308"
    assert not frame.empty


def test_fetch_us_symbol_maps_to_eastmoney_hist(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_spot_em():
        return pd.DataFrame({"代码": ["105.AAPL"]})

    def fake_us_hist(*, symbol: str, period: str, start_date: str, end_date: str, adjust: str):
        calls["hist"] = symbol
        return pd.DataFrame(
            {
                "date": ["2024-01-02"],
                "open": [1.0],
                "high": [1.0],
                "low": [1.0],
                "close": [1.0],
            }
        )

    def fake_us_daily(*, symbol: str, adjust: str):
        calls["daily"] = symbol
        return pd.DataFrame()

    monkeypatch.setattr(akshare_client.ak, "stock_us_spot_em", fake_spot_em)
    monkeypatch.setattr(akshare_client.ak, "stock_us_hist", fake_us_hist)
    monkeypatch.setattr(akshare_client.ak, "stock_us_daily", fake_us_daily)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch("AAPL.US", "2024-01-01", "2024-01-10")

    assert calls["hist"] == "105.AAPL"
    assert "daily" not in calls
    assert not frame.empty


def test_fetch_us_symbol_uses_direct_code(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_spot_em():
        raise AssertionError("spot_em should not be called for explicit codes")

    def fake_us_hist(*, symbol: str, period: str, start_date: str, end_date: str, adjust: str):
        calls["hist"] = symbol
        return pd.DataFrame(
            {
                "date": ["2024-01-02"],
                "open": [1.0],
                "high": [1.0],
                "low": [1.0],
                "close": [1.0],
            }
        )

    monkeypatch.setattr(akshare_client.ak, "stock_us_spot_em", fake_spot_em)
    monkeypatch.setattr(akshare_client.ak, "stock_us_hist", fake_us_hist)
    monkeypatch.setattr(akshare_client.ak, "stock_us_daily", lambda **_: pd.DataFrame())

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch("105.AAPL", "2024-01-01", "2024-01-10")

    assert calls["hist"] == "105.AAPL"
    assert not frame.empty


def test_fetch_us_symbol_falls_back_to_daily_with_date_filter(monkeypatch) -> None:
    def fake_spot_em():
        return pd.DataFrame()

    def fake_us_hist(*, symbol: str, period: str, start_date: str, end_date: str, adjust: str):
        raise AssertionError("hist should not be called when mapping is missing")

    def fake_us_daily(*, symbol: str, adjust: str):
        return pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
                "open": [1.0, 2.0, 3.0, 4.0],
                "high": [1.0, 2.0, 3.0, 4.0],
                "low": [1.0, 2.0, 3.0, 4.0],
                "close": [1.0, 2.0, 3.0, 4.0],
            }
        )

    monkeypatch.setattr(akshare_client.ak, "stock_us_spot_em", fake_spot_em)
    monkeypatch.setattr(akshare_client.ak, "stock_us_hist", fake_us_hist)
    monkeypatch.setattr(akshare_client.ak, "stock_us_daily", fake_us_daily)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch("AAPL", "2024-01-02", "2024-01-03")

    assert frame["date"].tolist() == [
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-03"),
    ]


def test_us_symbol_map_cache(monkeypatch) -> None:
    calls = {"spot": 0}

    def fake_time():
        return 1000.0

    def fake_spot_em():
        calls["spot"] += 1
        return pd.DataFrame({"代码": ["105.AAPL"]})

    def fake_us_hist(*, symbol: str, period: str, start_date: str, end_date: str, adjust: str):
        return pd.DataFrame(
            {
                "date": ["2024-01-02"],
                "open": [1.0],
                "high": [1.0],
                "low": [1.0],
                "close": [1.0],
            }
        )

    monkeypatch.setattr(akshare_client.time, "time", fake_time)
    monkeypatch.setattr(akshare_client.ak, "stock_us_spot_em", fake_spot_em)
    monkeypatch.setattr(akshare_client.ak, "stock_us_hist", fake_us_hist)
    monkeypatch.setattr(akshare_client.ak, "stock_us_daily", lambda **_: pd.DataFrame())

    client = akshare_client.AkshareMarketDataClient()
    client.fetch("AAPL.US", "2024-01-01", "2024-01-10")
    client.fetch("AAPL.US", "2024-01-01", "2024-01-10")

    assert calls["spot"] == 1
