import pytest
from pydantic import ValidationError

from datetime import datetime

from models.mcp_tools import (
    FundamentalCnIndicatorsRequest,
    FundamentalUsIndicatorsRequest,
    FundamentalUsReportRequest,
    KlineBar,
    KlineRequest,
    MacdRequest,
    MaRequest,
    RsiRequest,
    VolumePoint,
    VolumeRequest,
)


def test_kline_limit_validation() -> None:
    with pytest.raises(ValidationError):
        KlineRequest(symbol="000001", limit=0)


def test_rsi_defaults() -> None:
    request = RsiRequest(symbol="000001", limit=5)
    assert request.period == 14
    assert request.period_type == "1d"


def test_ma_type_validation() -> None:
    with pytest.raises(ValidationError):
        MaRequest(symbol="000001", limit=5, ma_type="wma")


def test_macd_slow_period_validation() -> None:
    with pytest.raises(ValidationError):
        MacdRequest(symbol="000001", limit=5, fast_period=12, slow_period=10)


def test_offset_validation() -> None:
    with pytest.raises(ValidationError):
        KlineRequest(symbol="000001", limit=5, offset=-1)


def test_date_validation_allows_supported_formats() -> None:
    request = KlineRequest(
        symbol="000001",
        limit=5,
        start_date="2024-01-01",
        end_date="20240131",
    )
    assert request.start_date == "2024-01-01"
    assert request.end_date == "20240131"


def test_date_validation_rejects_invalid() -> None:
    with pytest.raises(ValidationError):
        KlineRequest(symbol="000001", limit=5, start_date="01-01-2024")


def test_period_type_validation() -> None:
    with pytest.raises(ValidationError):
        KlineRequest(symbol="000001", limit=5, period_type="weekly")


def test_timestamp_json_includes_timezone() -> None:
    bar = KlineBar(
        timestamp=datetime(2024, 1, 1, 0, 0, 0),
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
    )
    payload = bar.model_dump(mode="json")
    assert payload["timestamp"].endswith("+00:00")


def test_volume_request_defaults() -> None:
    request = VolumeRequest(symbol="000001", limit=5)
    assert request.offset == 0
    assert request.period_type == "1d"


def test_volume_request_invalid_limit() -> None:
    with pytest.raises(ValidationError):
        VolumeRequest(symbol="000001", limit=0)


def test_volume_point_timestamp_json_includes_timezone() -> None:
    point = VolumePoint(timestamp=datetime(2024, 1, 1, 0, 0, 0), volume=100.0)
    payload = point.model_dump(mode="json")
    assert payload["timestamp"].endswith("+00:00")


def test_fundamental_cn_request_defaults() -> None:
    request = FundamentalCnIndicatorsRequest(symbol="000001")
    assert request.indicator == "按报告期"
    assert request.limit == 200
    assert request.offset == 0


def test_fundamental_cn_request_indicator_validation() -> None:
    with pytest.raises(ValidationError):
        FundamentalCnIndicatorsRequest(symbol="000001", indicator="季度")


def test_fundamental_us_report_defaults() -> None:
    request = FundamentalUsReportRequest(stock="TSLA")
    assert request.symbol == "资产负债表"
    assert request.indicator == "年报"
    assert request.limit == 200


def test_fundamental_us_report_symbol_validation() -> None:
    with pytest.raises(ValidationError):
        FundamentalUsReportRequest(stock="TSLA", symbol="利润表")


def test_fundamental_us_indicators_indicator_validation() -> None:
    with pytest.raises(ValidationError):
        FundamentalUsIndicatorsRequest(symbol="TSLA", indicator="季度")


def test_fundamental_request_date_validation() -> None:
    request = FundamentalUsIndicatorsRequest(
        symbol="TSLA",
        start_date="2024-01-01",
        end_date="20240131",
    )
    assert request.start_date == "2024-01-01"
    assert request.end_date == "20240131"
