from __future__ import annotations

from models.mcp_tools import KlineResponse, MacdResponse, MaResponse, RsiResponse, VolumeResponse
from utils.mcp_formatting.common import _fmt_indicator, _format_header, _format_table


def format_kline_response(response: KlineResponse) -> str:
    lines = _format_header("trading_kline", response)
    rows = [
        (
            item.timestamp,
            item.open,
            item.high,
            item.low,
            item.close,
            item.volume,
        )
        for item in response.items
    ]
    lines.extend(
        _format_table(["timestamp", "open", "high", "low", "close", "volume"], rows)
    )
    return "\n".join(lines)


def format_rsi_response(response: RsiResponse) -> str:
    lines = _format_header("trading_rsi", response)
    rows = [(item.timestamp, _fmt_indicator(item.rsi)) for item in response.items]
    lines.extend(_format_table(["timestamp", "rsi"], rows))
    return "\n".join(lines)


def format_ma_response(response: MaResponse) -> str:
    lines = _format_header("trading_ma", response)
    rows = [(item.timestamp, _fmt_indicator(item.ma)) for item in response.items]
    lines.extend(_format_table(["timestamp", "ma"], rows))
    return "\n".join(lines)


def format_macd_response(response: MacdResponse) -> str:
    lines = _format_header("trading_macd", response)
    rows = [
        (
            item.timestamp,
            _fmt_indicator(item.macd),
            _fmt_indicator(item.signal),
            _fmt_indicator(item.histogram),
        )
        for item in response.items
    ]
    lines.extend(_format_table(["timestamp", "macd", "signal", "histogram"], rows))
    return "\n".join(lines)


def format_volume_response(response: VolumeResponse) -> str:
    lines = _format_header("trading_volume", response)
    lines.append(
        "Units: "
        f"volume={response.volume_unit}, "
        f"amount={response.amount_unit or '-'}, "
        f"turnover_rate={response.turnover_rate_unit}"
    )
    lines.append("")
    rows = [
        (item.timestamp, item.volume, item.amount, item.turnover_rate)
        for item in response.items
    ]
    lines.extend(
        _format_table(["timestamp", "volume", "amount", "turnover_rate"], rows)
    )
    return "\n".join(lines)
