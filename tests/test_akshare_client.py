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

    def fake_hist_tx(*, symbol: str, start_date: str, end_date: str, adjust: str):
        calls["hist_tx"] = symbol
        return pd.DataFrame({
            "date": ["2024-01-01"],
            "open": [1.0],
            "high": [1.0],
            "low": [1.0],
            "close": [1.0],
        })

    monkeypatch.setattr(akshare_client.ak, "stock_zh_a_hist", fake_hist)
    monkeypatch.setattr(akshare_client.ak, "stock_zh_a_hist_tx", fake_hist_tx)
    monkeypatch.setattr(
        akshare_client.AkshareMarketDataClient,
        "_fetch_cn_tx_extended",
        lambda self, symbol, start_date, end_date: pd.DataFrame(),
    )

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch("300308.SZ", "2024-01-01", "2024-01-10")

    assert calls["hist"] == "300308"
    assert calls["hist_tx"] == "sz300308"
    assert not frame.empty


def test_fetch_falls_back_to_tencent_without_dates(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_hist(
        *, symbol: str, period: str, start_date: str, end_date: str, adjust: str
    ):
        calls["hist"] = symbol
        raise RuntimeError("primary source failed")

    def fake_hist_tx(*, symbol: str, start_date: str, end_date: str, adjust: str):
        calls["hist_tx"] = symbol
        calls["start_date"] = start_date
        calls["end_date"] = end_date
        return pd.DataFrame({
            "date": ["2024-01-01"],
            "open": [1.0],
            "high": [1.0],
            "low": [1.0],
            "close": [1.0],
        })

    monkeypatch.setattr(akshare_client.ak, "stock_zh_a_hist", fake_hist)
    monkeypatch.setattr(akshare_client.ak, "stock_zh_a_hist_tx", fake_hist_tx)
    monkeypatch.setattr(
        akshare_client.AkshareMarketDataClient,
        "_fetch_cn_tx_extended",
        lambda self, symbol, start_date, end_date: pd.DataFrame(),
    )

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch("000001")

    assert calls["hist"] == "000001"
    assert calls["hist_tx"] == "sz000001"
    assert len(calls["start_date"]) == 8
    assert len(calls["end_date"]) == 8
    assert not frame.empty


def test_fetch_cn_tencent_legacy_amount_maps_to_volume(monkeypatch) -> None:
    def fake_hist(
        *, symbol: str, period: str, start_date: str, end_date: str, adjust: str
    ):
        return pd.DataFrame()

    def fake_hist_tx(*, symbol: str, start_date: str, end_date: str, adjust: str):
        return pd.DataFrame({
            "date": ["2024-01-01"],
            "open": [1.0],
            "high": [1.1],
            "low": [0.9],
            "close": [1.0],
            "amount": [12345.0],
        })

    monkeypatch.setattr(akshare_client.ak, "stock_zh_a_hist", fake_hist)
    monkeypatch.setattr(akshare_client.ak, "stock_zh_a_hist_tx", fake_hist_tx)
    monkeypatch.setattr(
        akshare_client.AkshareMarketDataClient,
        "_fetch_cn_tx_extended",
        lambda self, symbol, start_date, end_date: pd.DataFrame(),
    )

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch("000001", "2024-01-01", "2024-01-10")

    assert frame["volume"].tolist() == [12345.0]
    assert "amount" not in frame.columns


def test_fetch_cn_prefers_extended_tencent_frame(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_hist(
        *, symbol: str, period: str, start_date: str, end_date: str, adjust: str
    ):
        return pd.DataFrame()

    def fake_hist_tx(*, symbol: str, start_date: str, end_date: str, adjust: str):
        calls["hist_tx"] = symbol
        return pd.DataFrame()

    def fake_extended(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        calls["extended"] = symbol
        return pd.DataFrame({
            "date": ["2024-01-01"],
            "open": [1.0],
            "high": [1.1],
            "low": [0.9],
            "close": [1.0],
            "volume": [1000.0],
            "amount": [1000000.0],
            "turnover_rate": [0.4],
        })

    monkeypatch.setattr(akshare_client.ak, "stock_zh_a_hist", fake_hist)
    monkeypatch.setattr(akshare_client.ak, "stock_zh_a_hist_tx", fake_hist_tx)
    monkeypatch.setattr(
        akshare_client.AkshareMarketDataClient,
        "_fetch_cn_tx_extended",
        fake_extended,
    )

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch("000001", "2024-01-01", "2024-01-10")

    assert calls["extended"] == "sz000001"
    assert "hist_tx" not in calls
    assert frame["volume"].tolist() == [1000.0]
    assert frame["amount"].tolist() == [1000000.0]
    assert frame["turnover_rate"].tolist() == [0.4]


def test_fetch_us_symbol_maps_to_eastmoney_hist(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_spot_em():
        return pd.DataFrame({"代码": ["105.AAPL"]})

    def fake_us_hist(
        *, symbol: str, period: str, start_date: str, end_date: str, adjust: str
    ):
        calls["hist"] = symbol
        return pd.DataFrame({
            "date": ["2024-01-02"],
            "open": [1.0],
            "high": [1.0],
            "low": [1.0],
            "close": [1.0],
        })

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
        return pd.DataFrame({
            "date": ["2024-01-02"],
            "open": [1.0],
            "high": [1.0],
            "low": [1.0],
            "close": [1.0],
        })

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
        return pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "open": [1.0, 2.0, 3.0, 4.0],
            "high": [1.0, 2.0, 3.0, 4.0],
            "low": [1.0, 2.0, 3.0, 4.0],
            "close": [1.0, 2.0, 3.0, 4.0],
        })

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
        return pd.DataFrame({
            "date": ["2024-01-02"],
            "open": [1.0],
            "high": [1.0],
            "low": [1.0],
            "close": [1.0],
        })

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

    def fake_us_hist(
        *, symbol: str, period: str, start_date: str, end_date: str, adjust: str
    ):
        raise AssertionError("hist should not be called when mapping is missing")

    def fake_us_daily(*, symbol: str, adjust: str):
        return pd.DataFrame({
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
        })

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
    assert frame["turnover_rate"].tolist() == pytest.approx([0.5, 0.5])


def test_fetch_us_resamples_monthly_from_daily(monkeypatch) -> None:
    def fake_spot_em():
        return pd.DataFrame()

    def fake_us_hist(
        *, symbol: str, period: str, start_date: str, end_date: str, adjust: str
    ):
        raise AssertionError("hist should not be called when mapping is missing")

    def fake_us_daily(*, symbol: str, adjust: str):
        return pd.DataFrame({
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
        })

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
    assert frame["turnover_rate"].tolist() == pytest.approx([0.5, 0.9])


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

    monkeypatch.setattr(
        akshare_client.ak, "stock_financial_us_report_em", fake_us_report
    )

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


def test_fetch_industry_summary_ths(monkeypatch) -> None:
    def fake_summary():
        return pd.DataFrame({"板块": ["元件"]})

    monkeypatch.setattr(
        akshare_client.ak, "stock_board_industry_summary_ths", fake_summary
    )

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_industry_summary_ths()

    assert frame["板块"].tolist() == ["元件"]


def test_fetch_fund_flow_individual_em_normalizes_symbol(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_individual(*, stock: str, market: str):
        calls["stock"] = stock
        calls["market"] = market
        return pd.DataFrame({
            "日期": ["2024-01-01"],
            "收盘价": [10.0],
            "涨跌幅": [1.0],
            "主力净流入-净额": [100.0],
            "主力净流入-净占比": [2.0],
        })

    monkeypatch.setattr(
        akshare_client.ak, "stock_individual_fund_flow", fake_individual
    )

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_fund_flow_individual_em("600094.SH")

    assert calls["stock"] == "600094"
    assert calls["market"] == "sh"
    assert frame["日期"].tolist() == [pd.Timestamp("2024-01-01")]


def test_fetch_fund_flow_individual_em_falls_back_to_eastmoney(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "data": {
                    "klines": [
                        "2024-01-01,100,10,20,30,40,1,2,3,4,5,10.5,1.1,0,0",
                        "2024-01-02,200,11,21,31,41,1.5,2.5,3.5,4.5,5.5,11.5,2.1,0,0",
                    ]
                }
            }

    def fake_individual(**_: object) -> pd.DataFrame:
        raise TypeError("shape changed")

    monkeypatch.setattr(
        akshare_client.ak,
        "stock_individual_fund_flow",
        fake_individual,
    )
    monkeypatch.setattr(akshare_client.requests, "get", lambda *_, **__: FakeResponse())

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_fund_flow_individual_em(
        "000001",
        start_date="2024-01-02",
        end_date="2024-01-02",
    )

    assert frame["日期"].tolist() == [pd.Timestamp("2024-01-02")]
    assert frame["主力净流入-净额"].tolist() == [200]


def test_fetch_fund_flow_sector_summary_unknown_board_raises(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "data": {"total": 1, "diff": [{"f12": "BK0001", "f14": "其他板块"}]}
            }

    def fake_summary(**_: object) -> pd.DataFrame:
        raise ValueError("upstream failure")

    monkeypatch.setattr(
        akshare_client.ak,
        "stock_sector_fund_flow_summary",
        fake_summary,
    )
    monkeypatch.setattr(akshare_client.requests, "get", lambda *_, **__: FakeResponse())

    client = akshare_client.AkshareMarketDataClient()
    with pytest.raises(MarketDataError, match="Unknown Eastmoney board symbol"):
        client.fetch_fund_flow_sector_summary_em("电源设备", "今日")


def test_fetch_industry_index_ths_normalizes_dates(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_index(*, symbol: str, start_date: str, end_date: str):
        calls["symbol"] = symbol
        calls["start_date"] = start_date
        calls["end_date"] = end_date
        return pd.DataFrame({"日期": ["2024-01-01"]})

    monkeypatch.setattr(akshare_client.ak, "stock_board_industry_index_ths", fake_index)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_industry_index_ths("元件", "2024-01-01", "2024-01-31")

    assert calls == {
        "symbol": "元件",
        "start_date": "20240101",
        "end_date": "20240131",
    }
    assert not frame.empty


def test_fetch_industry_name_em(monkeypatch) -> None:
    def fake_name():
        return pd.DataFrame({"板块名称": ["小金属"]})

    monkeypatch.setattr(akshare_client.ak, "stock_board_industry_name_em", fake_name)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_industry_name_em()

    assert frame["板块名称"].tolist() == ["小金属"]


def test_fetch_board_change_em(monkeypatch) -> None:
    def fake_board_change():
        return pd.DataFrame({"板块名称": ["融资融券"]})

    monkeypatch.setattr(akshare_client.ak, "stock_board_change_em", fake_board_change)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_board_change_em()

    assert frame["板块名称"].tolist() == ["融资融券"]


def test_fetch_industry_spot_em(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_spot(*, symbol: str):
        calls["symbol"] = symbol
        return pd.DataFrame({"最新": [1.0]})

    monkeypatch.setattr(akshare_client.ak, "stock_board_industry_spot_em", fake_spot)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_industry_spot_em("小金属")

    assert calls["symbol"] == "小金属"
    assert frame["最新"].tolist() == [1.0]


def test_fetch_industry_cons_em(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_cons(*, symbol: str):
        calls["symbol"] = symbol
        return pd.DataFrame({"代码": ["000001"]})

    monkeypatch.setattr(akshare_client.ak, "stock_board_industry_cons_em", fake_cons)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_industry_cons_em("小金属")

    assert calls["symbol"] == "小金属"
    assert frame["代码"].tolist() == ["000001"]


def test_fetch_industry_hist_em(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_hist(
        *, symbol: str, start_date: str, end_date: str, period: str, adjust: str
    ):
        calls["symbol"] = symbol
        calls["start_date"] = start_date
        calls["end_date"] = end_date
        calls["period"] = period
        calls["adjust"] = adjust
        return pd.DataFrame({"日期": ["2024-01-01"]})

    monkeypatch.setattr(akshare_client.ak, "stock_board_industry_hist_em", fake_hist)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_industry_hist_em(
        "小金属",
        "2024-01-01",
        "2024-01-31",
        period="周k",
        adjust="qfq",
    )

    assert calls == {
        "symbol": "小金属",
        "start_date": "20240101",
        "end_date": "20240131",
        "period": "周k",
        "adjust": "qfq",
    }
    assert not frame.empty


def test_fetch_industry_hist_min_em(monkeypatch) -> None:
    calls: dict[str, str] = {}

    def fake_hist_min(*, symbol: str, period: str):
        calls["symbol"] = symbol
        calls["period"] = period
        return pd.DataFrame({"时间": ["09:35"]})

    monkeypatch.setattr(
        akshare_client.ak,
        "stock_board_industry_hist_min_em",
        fake_hist_min,
    )

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_industry_hist_min_em("小金属", period="15")

    assert calls == {"symbol": "小金属", "period": "15"}
    assert frame["时间"].tolist() == ["09:35"]


def test_fetch_industry_summary_ths_wraps_error(monkeypatch) -> None:
    def fake_summary():
        raise RuntimeError("boom")

    monkeypatch.setattr(
        akshare_client.ak, "stock_board_industry_summary_ths", fake_summary
    )

    client = akshare_client.AkshareMarketDataClient()
    with pytest.raises(MarketDataError):
        client.fetch_industry_summary_ths()


def test_fetch_board_change_em_wraps_error(monkeypatch) -> None:
    monkeypatch.setattr(
        akshare_client.ak,
        "stock_board_change_em",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    client = akshare_client.AkshareMarketDataClient()
    with pytest.raises(MarketDataError):
        client.fetch_board_change_em()


def test_fetch_info_global_em(monkeypatch) -> None:
    def fake_info_global():
        return pd.DataFrame({"标题": ["快讯A"]})

    monkeypatch.setattr(akshare_client.ak, "stock_info_global_em", fake_info_global)

    client = akshare_client.AkshareMarketDataClient()
    frame = client.fetch_info_global_em()

    assert frame["标题"].tolist() == ["快讯A"]


def test_fetch_info_global_em_wraps_error(monkeypatch) -> None:
    monkeypatch.setattr(
        akshare_client.ak,
        "stock_info_global_em",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    client = akshare_client.AkshareMarketDataClient()
    with pytest.raises(MarketDataError):
        client.fetch_info_global_em()
