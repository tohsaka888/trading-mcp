from __future__ import annotations

from datetime import datetime

from models.mcp_tools import (
    FundamentalCnIndicatorsResponse,
    FundamentalUsIndicatorsResponse,
    FundamentalUsReportResponse,
    KlineBar,
    KlineResponse,
    MacdPoint,
    MacdResponse,
    MaPoint,
    MaResponse,
    RsiPoint,
    RsiResponse,
    VolumePoint,
    VolumeResponse,
)
from utils.mcp_formatting import (
    format_fundamental_cn_indicators_response,
    format_fundamental_us_indicators_response,
    format_fundamental_us_report_response,
    format_kline_response,
    format_macd_response,
    format_ma_response,
    format_rsi_response,
    format_volume_response,
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


def test_format_volume_response_contains_table_and_units() -> None:
    response = VolumeResponse(
        symbol="AAPL.US",
        items=[
            VolumePoint(
                timestamp=datetime(2024, 1, 1),
                volume=1000.0,
                amount=100000.0,
                turnover_rate=0.53,
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
        volume_unit="share",
        amount_unit="USD",
        turnover_rate_unit="percent",
    )
    text = format_volume_response(response)
    assert "# trading_volume" in text
    assert "Units: volume=share, amount=USD, turnover_rate=percent" in text
    assert "| timestamp | volume | amount | turnover_rate |" in text


def test_format_fundamental_cn_indicators_contains_preview() -> None:
    response = FundamentalCnIndicatorsResponse(
        symbol="000001",
        indicator="按报告期",
        count=1,
        total=1,
        limit=200,
        offset=0,
        has_more=False,
        next_offset=None,
        start_date="2024-01-01",
        end_date="2024-12-31",
        columns=["REPORT_DATE", "ROE"],
        items=[{"REPORT_DATE": "2024-12-31T00:00:00", "ROE": 10.5}],
    )
    text = format_fundamental_cn_indicators_response(response)
    assert "# trading_fundamental_cn_indicators" in text
    assert "Columns total: 2" in text
    assert "Full rows are available in structuredContent.items." in text


def test_format_fundamental_us_report_contains_context() -> None:
    response = FundamentalUsReportResponse(
        stock="TSLA",
        symbol="资产负债表",
        indicator="年报",
        count=1,
        total=1,
        limit=200,
        offset=0,
        has_more=False,
        next_offset=None,
        start_date=None,
        end_date=None,
        columns=["REPORT_DATE", "ITEM_NAME", "AMOUNT"],
        items=[
            {
                "REPORT_DATE": "2024-12-31T00:00:00",
                "ITEM_NAME": "Total Assets",
                "AMOUNT": 120.0,
            }
        ],
    )
    text = format_fundamental_us_report_response(response)
    assert "# trading_fundamental_us_report" in text
    assert "Stock: `TSLA`" in text
    assert "Report: `资产负债表` | Indicator: `年报`" in text


def test_format_fundamental_us_indicators_truncates_columns() -> None:
    columns = [f"c{i}" for i in range(1, 15)]
    response = FundamentalUsIndicatorsResponse(
        symbol="TSLA",
        indicator="年报",
        count=1,
        total=1,
        limit=200,
        offset=0,
        has_more=False,
        next_offset=None,
        start_date=None,
        end_date=None,
        columns=columns,
        items=[{column: column for column in columns}],
    )
    text = format_fundamental_us_indicators_response(response)
    assert "# trading_fundamental_us_indicators" in text
    assert "Only first 12 columns are shown in markdown." in text
