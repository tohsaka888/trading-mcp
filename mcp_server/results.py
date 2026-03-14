from __future__ import annotations

import json
from typing import Any, Callable, Literal, TypeVar

from mcp.types import CallToolResult, TextContent
from pydantic import BaseModel

ResponseT = TypeVar("ResponseT", bound=BaseModel)


def error_result(message: str) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        isError=True,
    )


def structured_error_result(message: str, response: BaseModel) -> CallToolResult:
    structured = response.model_dump(mode="json", by_alias=True)
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        structuredContent=structured,
        isError=True,
    )


def success_result(
    response: BaseModel,
    response_format: Literal["markdown", "json"],
    formatter: Callable[[Any], str],
) -> CallToolResult:
    structured = response.model_dump(mode="json", by_alias=True)
    if response_format == "json":
        text = json.dumps(structured, indent=2, ensure_ascii=False)
    else:
        text = formatter(response)
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        structuredContent=structured,
    )


def empty_table_response(
    response_cls: type[ResponseT],
    *,
    limit: int,
    offset: int,
    start_date: str | None = None,
    end_date: str | None = None,
    **kwargs: Any,
) -> ResponseT:
    return response_cls(
        count=0,
        total=0,
        limit=limit,
        offset=offset,
        has_more=False,
        next_offset=None,
        start_date=start_date,
        end_date=end_date,
        columns=[],
        items=[],
        **kwargs,
    )


def empty_tool_response(
    response_cls: type[ResponseT],
    *,
    symbol: str,
    limit: int,
    offset: int,
    period_type: str,
    start_date: str | None = None,
    end_date: str | None = None,
    **kwargs: Any,
) -> ResponseT:
    return response_cls(
        symbol=symbol,
        count=0,
        total=0,
        limit=limit,
        offset=offset,
        has_more=False,
        next_offset=None,
        period_type=period_type,
        start_date=start_date,
        end_date=end_date,
        items=[],
        **kwargs,
    )
