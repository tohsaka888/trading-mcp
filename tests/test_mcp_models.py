import pytest
from pydantic import ValidationError

from datetime import datetime

from models.mcp_tools import KlineBar, KlineRequest, MacdRequest, MaRequest, RsiRequest


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
