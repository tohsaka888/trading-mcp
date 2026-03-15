from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import pytest

from data.client import DateLike, MarketDataError
from models.mcp_tools import (
    BoardChangeEmRequest,
    FundFlowIndividualEmRequest,
    FundFlowIndividualRankEmRequest,
    FundFlowSectorRankEmRequest,
    FundFlowSectorSummaryEmRequest,
    FundamentalCnIndicatorsRequest,
    InfoGlobalEmRequest,
    FundamentalUsIndicatorsRequest,
    FundamentalUsReportRequest,
    IndustryConsEmRequest,
    IndustryHistEmRequest,
    IndustryHistMinEmRequest,
    IndustryIndexThsRequest,
    IndustryNameEmRequest,
    IndustrySpotEmRequest,
    IndustrySummaryThsRequest,
    KlineRequest,
    MacdRequest,
    MaRequest,
    RsiRequest,
    VolumeRequest,
)
from services.market_service import MarketService


class FakeClient:
    def __init__(self) -> None:
        self.last_period_type: str | None = None
        self.last_end: DateLike | None = None

    def fetch(
        self,
        symbol: str,
        start: DateLike | None = None,
        end: DateLike | None = None,
        period_type: str = "1d",
    ) -> pd.DataFrame:
        self.last_period_type = period_type
        self.last_end = end
        return pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "open": [10, 11, 12],
            "high": [11, 12, 13],
            "low": [9, 10, 11],
            "close": [10.5, 11.5, 12.5],
            "volume": [1000, 1100, 1200],
            "amount": [10000, 11000, 12000],
            "turnover_rate": [0.1, 0.2, 0.3],
        })

    def fetch_cn_financial_indicators(
        self, symbol: str, indicator: str
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_us_financial_report(
        self, stock: str, symbol: str, indicator: str
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_us_financial_indicators(
        self, symbol: str, indicator: str
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_industry_summary_ths(self) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_fund_flow_individual_em(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_fund_flow_individual_rank_em(self, indicator: str) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_fund_flow_sector_rank_em(
        self, indicator: str, sector_type: str
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_fund_flow_sector_summary_em(
        self, symbol: str, indicator: str
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_industry_index_ths(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_industry_name_em(self) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_board_change_em(self) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_industry_spot_em(self, symbol: str) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_industry_cons_em(self, symbol: str) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_industry_hist_em(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
        period: str = "日k",
        adjust: str = "",
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_industry_hist_min_em(
        self, symbol: str, period: str = "5"
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_info_global_em(self) -> pd.DataFrame:
        return pd.DataFrame()


class FakeEngine:
    def compute(
        self, name: str, series: pd.Series[Any], **kwargs: object
    ) -> pd.Series[int]:
        return pd.Series(range(len(series)), index=series.index, name=name)

    def compute_ma(
        self,
        series: pd.Series[Any],
        *,
        timeperiod: int = 20,
        matype: Any = 0,
    ) -> pd.Series[int]:
        return pd.Series(range(len(series)), index=series.index, name="ma")

    def compute_macd(self, series: pd.Series[Any], **kwargs: object) -> pd.DataFrame:
        values = list(range(len(series)))
        return pd.DataFrame(
            {
                "macd": values,
                "signal": values,
                "histogram": values,
            },
            index=series.index,
        )


def test_kline_limits_bars() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.kline(KlineRequest(symbol="000001", limit=2))
    assert response.count == 2
    assert response.total == 3
    assert response.has_more is True
    assert response.next_offset == 2
    assert len(response.items) == 2
    assert response.items[0].timestamp == datetime(2024, 1, 2)
    assert response.items[0].open == 11.0
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_rsi_points_limit() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.rsi(RsiRequest(symbol="000001", limit=2))
    assert response.count == 2
    assert response.total == 3
    assert len(response.items) == 2
    assert response.items[-1].timestamp == datetime(2024, 1, 3)
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_weekly_request_defaults_end_date_to_today() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.kline(KlineRequest(symbol="000001", limit=2, period_type="1w"))
    assert response.end_date is not None
    assert client.last_end == response.end_date


def test_ma_points_limit() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.ma(MaRequest(symbol="000001", limit=1))
    assert response.count == 1
    assert response.total == 3
    assert response.has_more is True
    assert response.next_offset == 1
    assert len(response.items) == 1
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_macd_points_limit() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.macd(MacdRequest(symbol="000001", limit=1))
    assert response.count == 1
    assert response.total == 3
    assert len(response.items) == 1
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_pagination_offset_beyond_total() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.kline(KlineRequest(symbol="000001", limit=2, offset=5))
    assert response.count == 0
    assert response.total == 3
    assert response.has_more is False
    assert response.next_offset is None
    assert response.items == []
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_volume_points_limit_and_units() -> None:
    client = FakeClient()
    service = MarketService(client, FakeEngine())
    response = service.volume(VolumeRequest(symbol="AAPL.US", limit=2))

    assert response.count == 2
    assert response.total == 3
    assert len(response.items) == 2
    assert response.items[0].timestamp == datetime(2024, 1, 2)
    assert response.items[0].volume == 1100.0
    assert response.volume_unit == "share"
    assert response.amount_unit == "USD"
    assert response.turnover_rate_unit == "percent"
    assert response.period_type == "1d"
    assert client.last_period_type == "1d"


def test_volume_missing_amount_turnover_defaults_none() -> None:
    class MissingFieldsClient(FakeClient):
        def fetch(
            self,
            symbol: str,
            start: DateLike | None = None,
            end: DateLike | None = None,
            period_type: str = "1d",
        ) -> pd.DataFrame:
            self.last_period_type = period_type
            return pd.DataFrame({
                "date": ["2024-01-01", "2024-01-02"],
                "volume": [1000, 1100],
            })

    client = MissingFieldsClient()
    service = MarketService(client, FakeEngine())
    response = service.volume(VolumeRequest(symbol="AAPL", limit=2))

    assert response.count == 2
    assert response.amount_unit is None
    assert response.items[0].amount is None
    assert response.items[0].turnover_rate is None


class FakeFundamentalClient(FakeClient):
    def fetch_cn_financial_indicators(
        self, symbol: str, indicator: str
    ) -> pd.DataFrame:
        return pd.DataFrame({
            "REPORT_DATE": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
            ],
            "ROE": [1.0, 2.0, float("nan"), 4.0],
            "NOTE": ["a", "b", "c", "d"],
        })

    def fetch_us_financial_report(
        self, stock: str, symbol: str, indicator: str
    ) -> pd.DataFrame:
        return pd.DataFrame({
            "REPORT_DATE": ["2023-12-31", "2024-12-31"],
            "ITEM_NAME": ["Total Assets", "Total Assets"],
            "AMOUNT": [100.0, 120.0],
        })

    def fetch_us_financial_indicators(
        self, symbol: str, indicator: str
    ) -> pd.DataFrame:
        return pd.DataFrame({
            "REPORT_DATE": ["2024-03-31", "2024-06-30"],
            "ROA": [0.11, 0.12],
        })

    def fetch_industry_summary_ths(self) -> pd.DataFrame:
        return pd.DataFrame({
            "板块": ["元件", "小金属", "风电设备"],
            "涨跌幅": [1.0, 2.0, 3.0],
        })

    def fetch_fund_flow_individual_em(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
    ) -> pd.DataFrame:
        return pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-03", "2024-01-02"],
            "收盘价": [10.0, 12.0, 11.0],
            "主力净流入-净额": [100.0, 300.0, 200.0],
        })

    def fetch_fund_flow_individual_rank_em(self, indicator: str) -> pd.DataFrame:
        return pd.DataFrame({
            "序号": [1, 2, 3],
            "代码": ["000001", "000002", "000003"],
            "名称": ["平安银行", "万科A", "国农科技"],
            f"{indicator}主力净流入-净额": [30.0, 20.0, 10.0],
        })

    def fetch_fund_flow_sector_rank_em(
        self, indicator: str, sector_type: str
    ) -> pd.DataFrame:
        return pd.DataFrame({
            "序号": [1, 2, 3],
            "名称": ["电源设备", "小金属", "元件"],
            f"{indicator}涨跌幅": [1.0, 3.0, 2.0],
            f"{indicator}主力净流入-净额": [300.0, 200.0, 100.0],
        })

    def fetch_fund_flow_sector_summary_em(
        self, symbol: str, indicator: str
    ) -> pd.DataFrame:
        return pd.DataFrame({
            "序号": [1, 2, 3],
            "代码": ["000001", "000002", "000003"],
            "名称": ["甲", "乙", "丙"],
            f"{indicator}主力净流入-净额": [10.0, 8.0, 6.0],
        })

    def fetch_industry_index_ths(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
    ) -> pd.DataFrame:
        return pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-03", "2024-01-02"],
            "收盘价": [10.0, 12.0, 11.0],
        })

    def fetch_industry_name_em(self) -> pd.DataFrame:
        return pd.DataFrame({"板块名称": ["元件", "小金属"]})

    def fetch_board_change_em(self) -> pd.DataFrame:
        return pd.DataFrame({
            "板块名称": ["融资融券", "深股通", "创业板综"],
            "板块异动总次数": [12, 10, 8],
        })

    def fetch_industry_spot_em(self, symbol: str) -> pd.DataFrame:
        return pd.DataFrame({"板块名称": [symbol], "最新": [123.4]})

    def fetch_industry_cons_em(self, symbol: str) -> pd.DataFrame:
        return pd.DataFrame({
            "板块名称": [symbol, symbol],
            "代码": ["000001", "000002"],
        })

    def fetch_industry_hist_em(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
        period: str = "日k",
        adjust: str = "",
    ) -> pd.DataFrame:
        return pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-03", "2024-01-02"],
            "收盘": [10.0, 12.0, 11.0],
        })

    def fetch_industry_hist_min_em(
        self, symbol: str, period: str = "5"
    ) -> pd.DataFrame:
        return pd.DataFrame({
            "时间": ["09:35", "09:40", "09:45"],
            "最新价": [10.0, 10.2, 10.3],
        })

    def fetch_info_global_em(self) -> pd.DataFrame:
        return pd.DataFrame({
            "标题": ["快讯A", "快讯B", "快讯C"],
            "发布时间": [
                "2024-03-13 10:00:00",
                "2024-03-13 09:59:00",
                "2024-03-13 09:58:00",
            ],
        })


def test_fundamental_cn_indicators_pagination_date_filter_and_nan() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fundamental_cn_indicators(
        FundamentalCnIndicatorsRequest(
            symbol="000001",
            indicator="按报告期",
            limit=2,
            offset=1,
            start_date="2024-01-01",
            end_date="2024-01-04",
        )
    )

    assert response.total == 4
    assert response.count == 2
    assert response.has_more is True
    assert response.next_offset == 3
    assert response.columns == ["REPORT_DATE", "ROE", "NOTE"]
    assert response.items[0]["REPORT_DATE"] == "2024-01-02T00:00:00"
    assert response.items[1]["ROE"] is None


def test_fund_flow_individual_em_filters_and_uses_latest_pagination() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fund_flow_individual_em(
        FundFlowIndividualEmRequest(
            symbol="000001",
            limit=1,
            offset=0,
            start_date="2024-01-02",
            end_date="2024-01-03",
        )
    )

    assert response.symbol == "000001"
    assert response.total == 2
    assert response.count == 1
    assert response.items[0]["日期"] == "2024-01-03T00:00:00"


def test_fund_flow_individual_rank_uses_head_pagination() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fund_flow_individual_rank_em(
        FundFlowIndividualRankEmRequest(indicator="5日", limit=1, offset=1)
    )

    assert response.indicator == "5日"
    assert response.total == 3
    assert response.count == 1
    assert response.items[0]["代码"] == "000002"


def test_fund_flow_sector_rank_sorts_by_change_pct_by_default() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fund_flow_sector_rank_em(
        FundFlowSectorRankEmRequest(
            indicator="今日",
            sector_type="行业资金流",
            limit=2,
            offset=0,
        )
    )

    assert response.indicator == "今日"
    assert response.sector_type == "行业资金流"
    assert response.sort_by == "涨跌幅"
    assert response.count == 2
    assert response.items[0]["名称"] == "小金属"
    assert response.items[1]["名称"] == "元件"


def test_fund_flow_sector_rank_sorts_by_main_net_inflow_when_requested() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fund_flow_sector_rank_em(
        FundFlowSectorRankEmRequest(
            indicator="今日",
            sector_type="行业资金流",
            sort_by="主力净流入",
            limit=2,
            offset=0,
        )
    )

    assert response.count == 2
    assert response.items[0]["名称"] == "电源设备"
    assert response.items[1]["名称"] == "小金属"


def test_fund_flow_sector_rank_paginates_after_sorting() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fund_flow_sector_rank_em(
        FundFlowSectorRankEmRequest(
            indicator="今日",
            sector_type="行业资金流",
            limit=1,
            offset=1,
        )
    )

    assert response.count == 1
    assert response.items[0]["名称"] == "元件"


def test_fund_flow_sector_rank_sorts_percent_strings() -> None:
    class PercentClient(FakeFundamentalClient):
        def fetch_fund_flow_sector_rank_em(
            self, indicator: str, sector_type: str
        ) -> pd.DataFrame:
            return pd.DataFrame({
                "序号": [1, 2, 3],
                "名称": ["电源设备", "小金属", "元件"],
                "阶段涨跌幅": ["1.2%", "1,234.5%", "3.4%"],
                "净额": [1.0, 2.0, 3.0],
            })

    service = MarketService(PercentClient(), FakeEngine())
    response = service.fund_flow_sector_rank_em(
        FundFlowSectorRankEmRequest(
            indicator="10日",
            sector_type="行业资金流",
            limit=3,
        )
    )

    assert [item["名称"] for item in response.items] == ["小金属", "元件", "电源设备"]


def test_fund_flow_sector_rank_raises_when_sort_column_missing() -> None:
    class MissingSortClient(FakeFundamentalClient):
        def fetch_fund_flow_sector_rank_em(
            self, indicator: str, sector_type: str
        ) -> pd.DataFrame:
            return pd.DataFrame({
                "序号": [1],
                "名称": ["电源设备"],
            })

    service = MarketService(MissingSortClient(), FakeEngine())

    with pytest.raises(
        MarketDataError,
        match=(
            "Sector rank sorting failed for indicator=今日, "
            "sector_type=行业资金流, sort_by=涨跌幅"
        ),
    ):
        service.fund_flow_sector_rank_em(
            FundFlowSectorRankEmRequest(
                indicator="今日",
                sector_type="行业资金流",
            )
        )


def test_fund_flow_sector_summary_uses_head_pagination() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fund_flow_sector_summary_em(
        FundFlowSectorSummaryEmRequest(
            symbol="电源设备",
            indicator="今日",
            limit=1,
            offset=2,
        )
    )

    assert response.symbol == "电源设备"
    assert response.indicator == "今日"
    assert response.count == 1
    assert response.items[0]["代码"] == "000003"


def test_fundamental_us_report_fields_and_date_filter() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fundamental_us_report(
        FundamentalUsReportRequest(
            stock="TSLA",
            symbol="资产负债表",
            indicator="年报",
            limit=5,
            start_date="2024-01-01",
            end_date="2024-12-31",
        )
    )

    assert response.stock == "TSLA"
    assert response.symbol == "资产负债表"
    assert response.indicator == "年报"
    assert response.total == 1
    assert response.items[0]["ITEM_NAME"] == "Total Assets"


def test_fundamental_us_indicators_returns_records() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.fundamental_us_indicators(
        FundamentalUsIndicatorsRequest(
            symbol="TSLA",
            indicator="年报",
            limit=1,
        )
    )

    assert response.symbol == "TSLA"
    assert response.indicator == "年报"
    assert response.total == 2
    assert response.count == 1
    assert response.items[0]["REPORT_DATE"] == "2024-06-30T00:00:00"


def test_industry_summary_ths_pagination() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.industry_summary_ths(
        IndustrySummaryThsRequest(limit=2, offset=0)
    )

    assert response.total == 3
    assert response.count == 2
    assert response.has_more is True
    assert response.next_offset == 2
    assert response.items[0]["板块"] == "小金属"


def test_industry_index_ths_filters_and_sorts_by_date() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.industry_index_ths(
        IndustryIndexThsRequest(
            symbol="元件",
            limit=5,
            start_date="2024-01-02",
            end_date="2024-01-03",
        )
    )

    assert response.symbol == "元件"
    assert response.total == 2
    assert response.items[0]["日期"] == "2024-01-02T00:00:00"
    assert response.items[1]["日期"] == "2024-01-03T00:00:00"


def test_industry_name_em_returns_raw_records() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.industry_name_em(IndustryNameEmRequest(limit=2))

    assert response.columns == ["板块名称"]
    assert response.total == 2
    assert response.items[0]["板块名称"] == "元件"


def test_board_change_em_pagination() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.board_change_em(BoardChangeEmRequest(limit=2, offset=1))

    assert response.total == 3
    assert response.count == 2
    assert response.has_more is False
    assert response.items[0]["板块名称"] == "融资融券"


def test_industry_spot_em_returns_symbol_metadata() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.industry_spot_em(IndustrySpotEmRequest(symbol="小金属", limit=1))

    assert response.symbol == "小金属"
    assert response.total == 1
    assert response.items[0]["板块名称"] == "小金属"


def test_industry_cons_em_empty_frame_returns_empty_table() -> None:
    class EmptyIndustryClient(FakeFundamentalClient):
        def fetch_industry_cons_em(self, symbol: str) -> pd.DataFrame:
            return pd.DataFrame()

    client = EmptyIndustryClient()
    service = MarketService(client, FakeEngine())
    response = service.industry_cons_em(IndustryConsEmRequest(symbol="小金属", limit=5))

    assert response.symbol == "小金属"
    assert response.total == 0
    assert response.count == 0
    assert response.columns == []
    assert response.items == []


def test_industry_hist_em_preserves_period_and_adjust() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.industry_hist_em(
        IndustryHistEmRequest(
            symbol="小金属",
            period="周k",
            adjust="qfq",
            limit=2,
            start_date="2024-01-01",
            end_date="2024-01-03",
        )
    )

    assert response.symbol == "小金属"
    assert response.period == "周k"
    assert response.adjust == "qfq"
    assert response.count == 2
    assert response.items[0]["日期"] == "2024-01-02T00:00:00"


def test_industry_hist_min_em_pagination() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.industry_hist_min_em(
        IndustryHistMinEmRequest(symbol="小金属", period="15", limit=1, offset=1)
    )

    assert response.symbol == "小金属"
    assert response.period == "15"
    assert response.total == 3
    assert response.count == 1
    assert response.items[0]["时间"] == "09:40"


def test_info_global_em_pagination() -> None:
    client = FakeFundamentalClient()
    service = MarketService(client, FakeEngine())
    response = service.info_global_em(InfoGlobalEmRequest(limit=2))

    assert response.total == 3
    assert response.count == 2
    assert response.has_more is True
    assert response.next_offset == 2
    assert response.items[0]["标题"] == "快讯B"
