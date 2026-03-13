from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from data.client import DateLike
from models.mcp_tools import (
    FundamentalCnIndicatorsRequest,
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
        return pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "open": [10, 11, 12],
                "high": [11, 12, 13],
                "low": [9, 10, 11],
                "close": [10.5, 11.5, 12.5],
                "volume": [1000, 1100, 1200],
                "amount": [10000, 11000, 12000],
                "turnover_rate": [0.1, 0.2, 0.3],
            }
        )

    def fetch_cn_financial_indicators(self, symbol: str, indicator: str) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_us_financial_report(
        self, stock: str, symbol: str, indicator: str
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_us_financial_indicators(self, symbol: str, indicator: str) -> pd.DataFrame:
        return pd.DataFrame()

    def fetch_industry_summary_ths(self) -> pd.DataFrame:
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

    def fetch_industry_hist_min_em(self, symbol: str, period: str = "5") -> pd.DataFrame:
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

    def compute_macd(
        self, series: pd.Series[Any], **kwargs: object
    ) -> pd.DataFrame:
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
            return pd.DataFrame(
                {
                    "date": ["2024-01-01", "2024-01-02"],
                    "volume": [1000, 1100],
                }
            )

    client = MissingFieldsClient()
    service = MarketService(client, FakeEngine())
    response = service.volume(VolumeRequest(symbol="AAPL", limit=2))

    assert response.count == 2
    assert response.amount_unit is None
    assert response.items[0].amount is None
    assert response.items[0].turnover_rate is None


class FakeFundamentalClient(FakeClient):
    def fetch_cn_financial_indicators(self, symbol: str, indicator: str) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "REPORT_DATE": [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                ],
                "ROE": [1.0, 2.0, float("nan"), 4.0],
                "NOTE": ["a", "b", "c", "d"],
            }
        )

    def fetch_us_financial_report(
        self, stock: str, symbol: str, indicator: str
    ) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "REPORT_DATE": ["2023-12-31", "2024-12-31"],
                "ITEM_NAME": ["Total Assets", "Total Assets"],
                "AMOUNT": [100.0, 120.0],
            }
        )

    def fetch_us_financial_indicators(self, symbol: str, indicator: str) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "REPORT_DATE": ["2024-03-31", "2024-06-30"],
                "ROA": [0.11, 0.12],
            }
        )

    def fetch_industry_summary_ths(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "板块": ["元件", "小金属", "风电设备"],
                "涨跌幅": [1.0, 2.0, 3.0],
            }
        )

    def fetch_industry_index_ths(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
    ) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "日期": ["2024-01-01", "2024-01-03", "2024-01-02"],
                "收盘价": [10.0, 12.0, 11.0],
            }
        )

    def fetch_industry_name_em(self) -> pd.DataFrame:
        return pd.DataFrame({"板块名称": ["元件", "小金属"]})

    def fetch_industry_spot_em(self, symbol: str) -> pd.DataFrame:
        return pd.DataFrame({"板块名称": [symbol], "最新": [123.4]})

    def fetch_industry_cons_em(self, symbol: str) -> pd.DataFrame:
        return pd.DataFrame({"板块名称": [symbol, symbol], "代码": ["000001", "000002"]})

    def fetch_industry_hist_em(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
        period: str = "日k",
        adjust: str = "",
    ) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "日期": ["2024-01-01", "2024-01-03", "2024-01-02"],
                "收盘": [10.0, 12.0, 11.0],
            }
        )

    def fetch_industry_hist_min_em(self, symbol: str, period: str = "5") -> pd.DataFrame:
        return pd.DataFrame(
            {
                "时间": ["09:35", "09:40", "09:45"],
                "最新价": [10.0, 10.2, 10.3],
            }
        )


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
