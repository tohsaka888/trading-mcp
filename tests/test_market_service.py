from __future__ import annotations

from datetime import datetime

import pandas as pd

from models.mcp_tools import KlineRequest, MacdRequest, MaRequest, RsiRequest
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
