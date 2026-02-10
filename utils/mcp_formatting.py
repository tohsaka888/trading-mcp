from __future__ import annotations

from datetime import datetime
from typing import Iterable

from models.mcp_tools import (
    FundamentalCnIndicatorsResponse,
    FundamentalUsIndicatorsResponse,
    FundamentalUsReportResponse,
    KlineResponse,
    MacdResponse,
    MaResponse,
    RsiResponse,
    VolumeResponse,
)

_FUNDAMENTAL_PREVIEW_ROWS = 20
_FUNDAMENTAL_PREVIEW_COLUMNS = 12


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


def _format_fundamental_preview(
    columns: list[str], items: list[dict[str, object]]
) -> list[str]:
    if not columns:
        return ["No rows returned."]

    preview_columns = columns[:_FUNDAMENTAL_PREVIEW_COLUMNS]
    preview_items = items[:_FUNDAMENTAL_PREVIEW_ROWS]
    rows = [
        [item.get(column) for column in preview_columns]
        for item in preview_items
    ]

    lines: list[str] = []
    lines.append(f"Columns total: {len(columns)}")
    lines.append("Column preview: " + ", ".join(preview_columns))
    lines.append("")
    lines.append("Preview rows:")
    lines.extend(_format_table(preview_columns, rows))

    if len(columns) > _FUNDAMENTAL_PREVIEW_COLUMNS:
        lines.append(
            f"Only first {_FUNDAMENTAL_PREVIEW_COLUMNS} columns are shown in markdown."
        )
    if len(items) > _FUNDAMENTAL_PREVIEW_ROWS:
        lines.append(
            f"Only first {_FUNDAMENTAL_PREVIEW_ROWS} rows are shown in markdown."
        )
    lines.append("Full rows are available in structuredContent.items.")
    return lines


def format_fundamental_cn_indicators_response(
    response: FundamentalCnIndicatorsResponse,
) -> str:
    lines = [f"# trading_fundamental_cn_indicators"]
    lines.append(f"Symbol: `{response.symbol}`")
    lines.append(f"Indicator: `{response.indicator}`")
    lines.append(
        " | ".join(
            [
                f"Limit: {response.limit}",
                f"Offset: {response.offset}",
                f"Count: {response.count}",
                f"Total: {response.total}",
            ]
        )
    )
    lines.append(f"Has more: {response.has_more} | Next offset: {response.next_offset}")
    lines.append(
        f"Date range: {response.start_date or '-'} to {response.end_date or '-'}"
    )
    lines.append("")
    lines.extend(_format_fundamental_preview(response.columns, response.items))
    return "\n".join(lines)


def format_fundamental_us_report_response(response: FundamentalUsReportResponse) -> str:
    lines = [f"# trading_fundamental_us_report"]
    lines.append(f"Stock: `{response.stock}`")
    lines.append(f"Report: `{response.symbol}` | Indicator: `{response.indicator}`")
    lines.append(
        " | ".join(
            [
                f"Limit: {response.limit}",
                f"Offset: {response.offset}",
                f"Count: {response.count}",
                f"Total: {response.total}",
            ]
        )
    )
    lines.append(f"Has more: {response.has_more} | Next offset: {response.next_offset}")
    lines.append(
        f"Date range: {response.start_date or '-'} to {response.end_date or '-'}"
    )
    lines.append("")
    lines.extend(_format_fundamental_preview(response.columns, response.items))
    return "\n".join(lines)


def format_fundamental_us_indicators_response(
    response: FundamentalUsIndicatorsResponse,
) -> str:
    lines = [f"# trading_fundamental_us_indicators"]
    lines.append(f"Symbol: `{response.symbol}`")
    lines.append(f"Indicator: `{response.indicator}`")
    lines.append(
        " | ".join(
            [
                f"Limit: {response.limit}",
                f"Offset: {response.offset}",
                f"Count: {response.count}",
                f"Total: {response.total}",
            ]
        )
    )
    lines.append(f"Has more: {response.has_more} | Next offset: {response.next_offset}")
    lines.append(
        f"Date range: {response.start_date or '-'} to {response.end_date or '-'}"
    )
    lines.append("")
    lines.extend(_format_fundamental_preview(response.columns, response.items))
    return "\n".join(lines)
