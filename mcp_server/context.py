from __future__ import annotations

from dataclasses import dataclass

from mcp.types import ToolAnnotations

from services.market_service import MarketService


@dataclass(frozen=True)
class ServerContext:
    service: MarketService
    annotations: ToolAnnotations
