from __future__ import annotations

from datetime import datetime

from models.mcp_tools import (
    KlineBar,
    KlineResponse,
    MacdPoint,
    MacdResponse,
    MaPoint,
    MaResponse,
    RsiPoint,
    RsiResponse,
)
from utils.mcp_formatting import (
    format_kline_response,
    format_macd_response,
    format_ma_response,
    format_rsi_response,
)


def test_format_kline_response_contains_table() -> None:
    response = KlineResponse(
        symbol="000001",
        items=[
            KlineBar(
                timestamp=datetime(2024, 1, 1),
                open=10.0,
                high=11.0,
                low=9.0,
                close=10.5,
                volume=1000.0,
            )
        ],
        count=1,
        total=1,
        limit=1,
        offset=0,
        has_more=False,
        next_offset=None,
        period_type="1d",
        start_date="2024-01-01",
        end_date="2024-01-01",
    )
    text = format_kline_response(response)
    assert "# trading_kline" in text
    assert "Period: `1d`" in text
    assert "| timestamp | open | high | low | close | volume |" in text


def test_format_rsi_response_contains_table() -> None:
    response = RsiResponse(
        symbol="000001",
        items=[RsiPoint(timestamp=datetime(2024, 1, 1), rsi=50.0)],
        count=1,
        total=1,
        limit=1,
        offset=0,
        has_more=False,
        next_offset=None,
        period_type="1d",
        start_date=None,
        end_date=None,
    )
    text = format_rsi_response(response)
    assert "# trading_rsi" in text
    assert "Period: `1d`" in text
    assert "| timestamp | rsi |" in text


def test_format_ma_response_contains_table() -> None:
    response = MaResponse(
        symbol="000001",
        items=[MaPoint(timestamp=datetime(2024, 1, 1), ma=10.0)],
        count=1,
        total=1,
        limit=1,
        offset=0,
        has_more=False,
        next_offset=None,
        period_type="1d",
        start_date=None,
        end_date=None,
    )
    text = format_ma_response(response)
    assert "# trading_ma" in text
    assert "Period: `1d`" in text
    assert "| timestamp | ma |" in text


def test_format_macd_response_contains_table() -> None:
    response = MacdResponse(
        symbol="000001",
        items=[
            MacdPoint(
                timestamp=datetime(2024, 1, 1),
                macd=1.0,
                signal=0.5,
                histogram=0.2,
            )
        ],
        count=1,
        total=1,
        limit=1,
        offset=0,
        has_more=False,
        next_offset=None,
        period_type="1d",
        start_date=None,
        end_date=None,
    )
    text = format_macd_response(response)
    assert "# trading_macd" in text
    assert "Period: `1d`" in text
    assert "| timestamp | macd | signal | histogram |" in text
