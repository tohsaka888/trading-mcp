from __future__ import annotations

from models.mcp_tools import InfoGlobalEmResponse
from utils.mcp_formatting.common import format_table_response


def format_info_global_em_response(response: InfoGlobalEmResponse) -> str:
    return format_table_response("trading_info_global_em", response)
