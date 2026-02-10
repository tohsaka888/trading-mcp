from __future__ import annotations

import pandas as pd
import pytest

from data import akshare_client
from data.client import MarketDataError


def test_fetch_falls_back_to_tencent_with_normalized_symbol(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_hist(
        *, symbol: str, period: str, start_date: str, end_date: str, adjust: str
    ):
        calls["hist"] = symbol
        return pd.DataFrame()

    def fake_hist_tx(
        *, symbol: str, start_date: str, end_date: str, adjust: str
    ):
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

    def fake_us_hist(
        *, symbol: str, period: str, start_date: str, end_date: str, adjust: str
    ):
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

    def fake_us_hist(
        *, symbol: str, period: str, start_date: str, end_date: str, adjust: str
    ):
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

    def fake_us_hist(
        *, symbol: str, period: str, start_date: str, end_date: str, adjust: str
    ):
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

    def fake_us_hist(
        *, symbol: str, period: str, start_date: str, end_date: str, adjust: str
    ):
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


def test_fetch_us_resamples_weekly_from_daily(monkeypatch) -> None:
    def fake_spot_em():
        return pd.DataFrame()

    def fake_us_hist(*, symbol: str, period: str, start_date: str, end_date: str, adjust: str):
        raise AssertionError("hist should not be called when mapping is missing")

    def fake_us_daily(*, symbol: str, adjust: str):
        return pd.DataFrame(
            {
                "date": [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                    "2024-01-08",
                    "2024-01-09",
                    "2024-01-10",
                    "2024-01-11",
                    "2024-01-12",
                ],
                "open": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "high": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                "low": [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5],
                "close": [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1],
                "volume": [100, 100, 100, 100, 100, 200, 200, 200, 200, 200],
                "amount": [1000, 1000, 1000, 1000, 1000, 2000, 2000, 2000, 2000, 2000],
                "turnover_rate": [0.1] * 10,
            }
        )

    monkeypatch.setattr(akshare_client.ak, "stock_us_spot_em", fake_spot_em)
    monkeypatch.setattr(akshare_client.ak, "stock_us_hist", fake_us_hist)
    monkeypatch.setattr(akshare_client.ak, "stock_us_daily", fake_us_daily)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch("AAPL", "2024-01-01", "2024-01-31", period_type="1w")

    assert frame["date"].tolist() == [
        pd.Timestamp("2024-01-05"),
        pd.Timestamp("2024-01-12"),
    ]
    assert frame["open"].tolist() == [1, 6]
    assert frame["high"].tolist() == [6, 11]
    assert frame["low"].tolist() == [0.5, 5.5]
    assert frame["close"].tolist() == [5.1, 10.1]
    assert frame["volume"].tolist() == [500, 1000]
    assert frame["amount"].tolist() == [5000, 10000]
    assert "turnover_rate" not in frame.columns


def test_fetch_us_resamples_monthly_from_daily(monkeypatch) -> None:
    def fake_spot_em():
        return pd.DataFrame()

    def fake_us_hist(*, symbol: str, period: str, start_date: str, end_date: str, adjust: str):
        raise AssertionError("hist should not be called when mapping is missing")

    def fake_us_daily(*, symbol: str, adjust: str):
        return pd.DataFrame(
            {
                "date": [
                    "2024-01-30",
                    "2024-01-31",
                    "2024-02-01",
                    "2024-02-29",
                ],
                "open": [10, 11, 12, 13],
                "high": [11, 12, 13, 14],
                "low": [9, 10, 11, 12],
                "close": [10.5, 11.5, 12.5, 13.5],
                "volume": [100, 200, 300, 400],
                "amount": [1000, 2000, 3000, 4000],
                "turnover_rate": [0.2, 0.3, 0.4, 0.5],
            }
        )

    monkeypatch.setattr(akshare_client.ak, "stock_us_spot_em", fake_spot_em)
    monkeypatch.setattr(akshare_client.ak, "stock_us_hist", fake_us_hist)
    monkeypatch.setattr(akshare_client.ak, "stock_us_daily", fake_us_daily)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch("AAPL", "2024-01-01", "2024-02-29", period_type="1m")

    assert frame["date"].tolist() == [
        pd.Timestamp("2024-01-31"),
        pd.Timestamp("2024-02-29"),
    ]
    assert frame["open"].tolist() == [10, 12]
    assert frame["high"].tolist() == [12, 14]
    assert frame["low"].tolist() == [9, 11]
    assert frame["close"].tolist() == [11.5, 13.5]
    assert frame["volume"].tolist() == [300, 700]
    assert frame["amount"].tolist() == [3000, 7000]
    assert "turnover_rate" not in frame.columns


def test_fetch_cn_financial_indicators_normalizes_symbol(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_cn_indicators(*, symbol: str, indicator: str):
        calls["symbol"] = symbol
        calls["indicator"] = indicator
        return pd.DataFrame({"REPORT_DATE": ["2024-12-31"], "ROE": [12.3]})

    monkeypatch.setattr(
        akshare_client.ak,
        "stock_financial_analysis_indicator_em",
        fake_cn_indicators,
    )

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_cn_financial_indicators("000001", "按报告期")

    assert calls["symbol"] == "000001.SZ"
    assert calls["indicator"] == "按报告期"
    assert not frame.empty


def test_fetch_cn_financial_indicators_rejects_bj_symbol() -> None:
    client = akshare_client.AkshareMarketDataClient()
    with pytest.raises(MarketDataError):
        client.fetch_cn_financial_indicators("830799.BJ", "按报告期")


def test_fetch_us_financial_report_normalizes_stock(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_us_report(*, stock: str, symbol: str, indicator: str):
        calls["stock"] = stock
        calls["symbol"] = symbol
        calls["indicator"] = indicator
        return pd.DataFrame({"REPORT_DATE": ["2024-12-31"], "AMOUNT": [100.0]})

    monkeypatch.setattr(akshare_client.ak, "stock_financial_us_report_em", fake_us_report)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_us_financial_report("BRK.B", "资产负债表", "年报")

    assert calls["stock"] == "BRK_B"
    assert calls["symbol"] == "资产负债表"
    assert calls["indicator"] == "年报"
    assert not frame.empty


def test_fetch_us_financial_indicators_normalizes_symbol(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_us_indicators(*, symbol: str, indicator: str):
        calls["symbol"] = symbol
        calls["indicator"] = indicator
        return pd.DataFrame({"REPORT_DATE": ["2024-12-31"], "ROE": [10.2]})

    monkeypatch.setattr(
        akshare_client.ak,
        "stock_financial_us_analysis_indicator_em",
        fake_us_indicators,
    )

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_us_financial_indicators("105.AAPL", "年报")

    assert calls["symbol"] == "AAPL"
    assert calls["indicator"] == "年报"
    assert not frame.empty


def test_fetch_us_financial_indicators_wraps_errors(monkeypatch) -> None:
    def fake_us_indicators(*, symbol: str, indicator: str):
        raise TypeError("mock failure")

    monkeypatch.setattr(
        akshare_client.ak,
        "stock_financial_us_analysis_indicator_em",
        fake_us_indicators,
    )

    client = akshare_client.AkshareMarketDataClient()
    with pytest.raises(MarketDataError):
        client.fetch_us_financial_indicators("TSLA", "年报")
