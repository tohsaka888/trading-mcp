from __future__ import annotations

import json
from typing import Any, Callable, Literal

from mcp.types import CallToolResult, TextContent
from pydantic import BaseModel


def error_result(message: str) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
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
