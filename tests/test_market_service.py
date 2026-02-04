from __future__ import annotations

from datetime import datetime

import pandas as pd

from models.mcp_tools import KlineRequest, MacdRequest, MaRequest, RsiRequest
from services.market_service import MarketService


class FakeClient:
    def fetch(self, symbol: str, start=None, end=None) -> pd.DataFrame:  # type: ignore[override]
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
    service = MarketService(FakeClient(), FakeEngine())
    bars = service.kline(KlineRequest(symbol="000001", limit=2))
    assert len(bars) == 2
    assert bars[0].timestamp == datetime(2024, 1, 2)
    assert bars[0].open == 11.0


def test_rsi_points_limit() -> None:
    service = MarketService(FakeClient(), FakeEngine())
    points = service.rsi(RsiRequest(symbol="000001", limit=2))
    assert len(points) == 2
    assert points[-1].timestamp == datetime(2024, 1, 3)


def test_ma_points_limit() -> None:
    service = MarketService(FakeClient(), FakeEngine())
    points = service.ma(MaRequest(symbol="000001", limit=1))
    assert len(points) == 1


def test_macd_points_limit() -> None:
    service = MarketService(FakeClient(), FakeEngine())
    points = service.macd(MacdRequest(symbol="000001", limit=1))
    assert len(points) == 1
