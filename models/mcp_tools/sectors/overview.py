from __future__ import annotations

from pydantic import Field

from models.mcp_tools.common import TableRequest, TableResponse


class IndustrySummaryThsRequest(TableRequest):
    pass


class IndustryNameEmRequest(TableRequest):
    pass


class IndustrySpotEmRequest(TableRequest):
    symbol: str = Field(..., min_length=1, description="EM industry board symbol")


class IndustryConsEmRequest(TableRequest):
    symbol: str = Field(..., min_length=1, description="EM industry board symbol")


class IndustrySummaryThsResponse(TableResponse):
    pass


class IndustryNameEmResponse(TableResponse):
    pass


class IndustrySpotEmResponse(TableResponse):
    symbol: str = Field(..., min_length=1, description="EM industry board symbol")


class IndustryConsEmResponse(TableResponse):
    symbol: str = Field(..., min_length=1, description="EM industry board symbol")
