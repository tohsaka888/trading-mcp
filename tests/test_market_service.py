from __future__ import annotations

from datetime import datetime

import pandas as pd

from models.mcp_tools import (
    FundamentalCnIndicatorsRequest,
    FundamentalUsIndicatorsRequest,
    FundamentalUsReportRequest,
    KlineRequest,
    MacdRequest,
    MaRequest,
    RsiRequest,
    VolumeRequest,
)
from services.market_service import MarketService


class FakeClient:
    def __init__(self) -> None:
        self.last_period_type: str | None = None

    def fetch(
        self,
        symbol: str,
        start=None,
        end=None,
        period_type: str = "1d",
    ) -> pd.DataFrame:  # type: ignore[override]
        self.last_period_type = period_type
        return pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "open": [10, 11, 12],
                "high": [11, 12, 13],
                "low": [9, 10, 11],
                "close": [10.5, 11.5, 12.5],
                "volume": [1000, 1100, 1200],
                "amount": [10000, 11000, 12000],
                "turnover_rate": [0.1, 0.2, 0.3],
            }
        )


class FakeEngine:
    def compute(self, name: str, series: pd.Series, **kwargs):
        return pd.Series(range(len(series)), index=series.index, name=name)

    def compute_macd(self, series: pd.Series, **kwargs):
        values = list(range(len(series)))
        return pd.DataFrame(
            {
                "macd": values,
                "signal": values,
                "histogram": values,
            },
            index=series.index,
        )


def test_kline_limits_bars() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.kline(KlineRequest(symbol="000001", limit=2))
    assert response.count == 2
    assert response.total == 3
    assert response.has_more is True
    assert response.next_offset == 2
    assert len(response.items) == 2
    assert response.items[0].timestamp == datetime(2024, 1, 2)
    assert response.items[0].open == 11.0
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_rsi_points_limit() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.rsi(RsiRequest(symbol="000001", limit=2))
    assert response.count == 2
    assert response.total == 3
    assert len(response.items) == 2
    assert response.items[-1].timestamp == datetime(2024, 1, 3)
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_ma_points_limit() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.ma(MaRequest(symbol="000001", limit=1))
    assert response.count == 1
    assert response.total == 3
    assert response.has_more is True
    assert response.next_offset == 1
    assert len(response.items) == 1
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_macd_points_limit() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.macd(MacdRequest(symbol="000001", limit=1))
    assert response.count == 1
    assert response.total == 3
    assert len(response.items) == 1
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_pagination_offset_beyond_total() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.kline(KlineRequest(symbol="000001", limit=2, offset=5))
    assert response.count == 0
    assert response.total == 3
    assert response.has_more is False
    assert response.next_offset is None
    assert response.items == []
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_volume_points_limit_and_units() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.volume(VolumeRequest(symbol="AAPL.US", limit=2))

    assert response.count == 2
    assert response.total == 3
    assert len(response.items) == 2
    assert response.items[0].timestamp == datetime(2024, 1, 2)
    assert response.items[0].volume == 1100.0
    assert response.volume_unit == "share"
    assert response.amount_unit == "USD"
    assert response.turnover_rate_unit == "percent"
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_volume_missing_amount_turnover_defaults_none() -> None:
    class MissingFieldsClient(FakeClient):
        def fetch(self, symbol: str, start=None, end=None, period_type: str = "1d"):
            self.last_period_type = period_type
            return pd.DataFrame(
                {
                    "date": ["2024-01-01", "2024-01-02"],
                    "volume": [1000, 1100],
                }
            )

    client = MissingFieldsClient()
    service = MarketService(client, FakeEngine())
    response = service.volume(VolumeRequest(symbol="AAPL", limit=2))

    assert response.count == 2
    assert response.amount_unit is None
    assert response.items[0].amount is None
    assert response.items[0].turnover_rate is None


class FakeFundamentalClient(FakeClient):
    def fetch_cn_financial_indicators(self, symbol: str, indicator: str) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "REPORT_DATE": [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                ],
                "ROE": [1.0, 2.0, float("nan"), 4.0],
                "NOTE": ["a", "b", "c", "d"],
            }
        )

    def fetch_us_financial_report(
        self, stock: str, symbol: str, indicator: str
    ) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "REPORT_DATE": ["2023-12-31", "2024-12-31"],
                "ITEM_NAME": ["Total Assets", "Total Assets"],
                "AMOUNT": [100.0, 120.0],
            }
        )

    def fetch_us_financial_indicators(self, symbol: str, indicator: str) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "REPORT_DATE": ["2024-03-31", "2024-06-30"],
                "ROA": [0.11, 0.12],
            }
        )


def test_fundamental_cn_indicators_pagination_date_filter_and_nan() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fundamental_cn_indicators(
        FundamentalCnIndicatorsRequest(
            symbol="000001",
            indicator="按报告期",
            limit=2,
            offset=1,
            start_date="2024-01-01",
            end_date="2024-01-04",
        )
    )

    assert response.total == 4
    assert response.count == 2
    assert response.has_more is True
    assert response.next_offset == 3
    assert response.columns == ["REPORT_DATE", "ROE", "NOTE"]
    assert response.items[0]["REPORT_DATE"] == "2024-01-02T00:00:00"
    assert response.items[1]["ROE"] is None


def test_fundamental_us_report_fields_and_date_filter() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fundamental_us_report(
        FundamentalUsReportRequest(
            stock="TSLA",
            symbol="资产负债表",
            indicator="年报",
            limit=5,
            start_date="2024-01-01",
            end_date="2024-12-31",
        )
    )

    assert response.stock == "TSLA"
    assert response.symbol == "资产负债表"
    assert response.indicator == "年报"
    assert response.total == 1
    assert response.items[0]["ITEM_NAME"] == "Total Assets"


def test_fundamental_us_indicators_returns_records() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fundamental_us_indicators(
        FundamentalUsIndicatorsRequest(
            symbol="TSLA",
            indicator="年报",
            limit=1,
        )
    )

    assert response.symbol == "TSLA"
    assert response.indicator == "年报"
    assert response.total == 2
    assert response.count == 1
    assert response.items[0]["REPORT_DATE"] == "2024-06-30T00:00:00"
