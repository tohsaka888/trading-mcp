from __future__ import annotations

from datetime import date, datetime
from typing import Protocol, runtime_checkable

import pandas as pd

DateLike = date | datetime | str


class MarketDataError(RuntimeError):
    """Raised when market data operations fail."""


@runtime_checkable
class MarketDataClient(Protocol):
    """Interface for market data clients."""

    def fetch(
        self,
        symbol: str,
        start: DateLike | None = None,
        end: DateLike | None = None,
        period_type: str = "1d",
    ) -> pd.DataFrame:
        """Return time-ordered data for a symbol and date range."""

        raise NotImplementedError

    def fetch_cn_financial_indicators(
        self,
        symbol: str,
        indicator: str,
    ) -> pd.DataFrame:
        """Return A-share financial indicator records."""

        raise NotImplementedError

    def fetch_us_financial_report(
        self,
        stock: str,
        symbol: str,
        indicator: str,
    ) -> pd.DataFrame:
        """Return US financial report records."""

        raise NotImplementedError

    def fetch_us_financial_indicators(
        self,
        symbol: str,
        indicator: str,
    ) -> pd.DataFrame:
        """Return US financial indicator records."""

        raise NotImplementedError

    def fetch_industry_summary_ths(self) -> pd.DataFrame:
        """Return THS industry board summary records."""

        raise NotImplementedError

    def fetch_fund_flow_individual_em(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
    ) -> pd.DataFrame:
        """Return Eastmoney individual stock fund-flow records."""

        raise NotImplementedError

    def fetch_fund_flow_individual_rank_em(
        self,
        indicator: str,
    ) -> pd.DataFrame:
        """Return Eastmoney individual stock fund-flow ranking records."""

        raise NotImplementedError

    def fetch_fund_flow_sector_rank_em(
        self,
        indicator: str,
        sector_type: str,
    ) -> pd.DataFrame:
        """Return Eastmoney sector fund-flow ranking records."""

        raise NotImplementedError

    def fetch_fund_flow_sector_summary_em(
        self,
        symbol: str,
        indicator: str,
    ) -> pd.DataFrame:
        """Return Eastmoney sector constituent fund-flow records."""

        raise NotImplementedError

    def fetch_industry_index_ths(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
    ) -> pd.DataFrame:
        """Return THS industry board index records."""

        raise NotImplementedError

    def fetch_industry_name_em(self) -> pd.DataFrame:
        """Return EM industry board name records."""

        raise NotImplementedError

    def fetch_industry_spot_em(self, symbol: str) -> pd.DataFrame:
        """Return EM industry board spot records."""

        raise NotImplementedError

    def fetch_industry_cons_em(self, symbol: str) -> pd.DataFrame:
        """Return EM industry board constituent records."""

        raise NotImplementedError

    def fetch_industry_hist_em(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
        period: str = "日k",
        adjust: str = "",
    ) -> pd.DataFrame:
        """Return EM industry board historical K-line records."""

        raise NotImplementedError

    def fetch_industry_hist_min_em(
        self,
        symbol: str,
        period: str = "5",
    ) -> pd.DataFrame:
        """Return EM industry board intraday historical records."""

        raise NotImplementedError
