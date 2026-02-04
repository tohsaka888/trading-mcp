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
