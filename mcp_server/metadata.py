from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class ToolMeta:
    name: str
    signature: str
    resource_description: str
    resource_fields: list[str]


def build_tool_usage(tool_metas: list[ToolMeta]) -> str:
    lines = ["Available tools:"]
    lines.extend(f"- {tool.signature}" for tool in tool_metas)
    lines.extend([
        "period_type allowed values: '1d' | '1w' | '1m'. "
        "Use exact enum value, not 'daily/weekly/monthly'.",
        "Industry hist period values: '日k' | '周k' | '月k'; "
        "adjust values: 'none' | 'qfq' | 'hfq'; minute period values: "
        "'1' | '5' | '15' | '30' | '60'.",
        "Inputs require a positive limit and a non-empty symbol. "
        "US symbols: AAPL.US, AAPL, 105.AAPL, BRK.B.",
    ])
    return "\n".join(lines)


def build_indicator_resource(tool_metas: list[ToolMeta]) -> str:
    payload = {
        tool.name: {
            "description": tool.resource_description,
            "fields": tool.resource_fields,
        }
        for tool in tool_metas
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
