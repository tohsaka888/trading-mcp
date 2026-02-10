from __future__ import annotations

from datetime import datetime
from typing import Iterable

from models.mcp_tools import (
    KlineResponse,
    MacdResponse,
    MaResponse,
    RsiResponse,
    VolumeResponse,
)


def _fmt_value(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _fmt_indicator(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


def _format_header(tool_name: str, response: object) -> list[str]:
    lines: list[str] = [f"# {tool_name}"]
    symbol = getattr(response, "symbol", "-")
    period_type = getattr(response, "period_type", "-")
    limit = getattr(response, "limit", "-")
    offset = getattr(response, "offset", "-")
    count = getattr(response, "count", "-")
    total = getattr(response, "total", "-")
    has_more = getattr(response, "has_more", "-")
    next_offset = getattr(response, "next_offset", "-")
    start_date = getattr(response, "start_date", None) or "-"
    end_date = getattr(response, "end_date", None) or "-"

    lines.append(f"Symbol: `{symbol}`")
    lines.append(f"Period: `{period_type}`")
    lines.append(
        " | ".join(
            [
                f"Limit: {limit}",
                f"Offset: {offset}",
                f"Count: {count}",
                f"Total: {total}",
            ]
        )
    )
    lines.append(f"Has more: {has_more} | Next offset: {next_offset}")
    lines.append(f"Date range: {start_date} to {end_date}")
    lines.append("")
    return lines


def _format_table(headers: Iterable[str], rows: Iterable[Iterable[object]]) -> list[str]:
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join("---" for _ in headers) + " |"
    body_rows = [
        "| " + " | ".join(_fmt_value(value) for value in row) + " |" for row in rows
    ]
    return [header_row, separator_row, *body_rows]


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
    lines.extend(_format_table(["timestamp", "volume", "amount", "turnover_rate"], rows))
    return "\n".join(lines)
