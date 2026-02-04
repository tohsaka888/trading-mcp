import pytest
from pydantic import ValidationError

from models.mcp_tools import KlineRequest, MacdRequest, MaRequest, RsiRequest


def test_kline_limit_validation() -> None:
    with pytest.raises(ValidationError):
        KlineRequest(symbol="000001", limit=0)


def test_rsi_defaults() -> None:
    request = RsiRequest(symbol="000001", limit=5)
    assert request.period == 14


def test_ma_type_validation() -> None:
    with pytest.raises(ValidationError):
        MaRequest(symbol="000001", limit=5, ma_type="wma")


def test_macd_slow_period_validation() -> None:
    with pytest.raises(ValidationError):
        MacdRequest(symbol="000001", limit=5, fast_period=12, slow_period=10)
