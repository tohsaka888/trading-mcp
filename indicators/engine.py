from __future__ import annotations

from typing import Callable, Mapping, Sequence

import numpy as np
import pandas as pd
import talib


class IndicatorError(ValueError):
    """Raised when indicator computation fails."""


def _default_registry() -> dict[str, Callable[..., np.ndarray]]:
    return {
        "sma": talib.SMA,
        "ema": talib.EMA,
        "ma": talib.MA,
        "rsi": talib.RSI,
    }


def _to_numpy(values: Sequence[float] | pd.Series) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise IndicatorError("Indicator input must be one-dimensional")
    return array


class IndicatorEngine:
    """Indicator computation wrapper with a supported-indicator registry."""

    def __init__(self, registry: Mapping[str, Callable[..., np.ndarray]] | None = None) -> None:
        source = registry or _default_registry()
        self._registry = {name.lower(): func for name, func in source.items()}

    def supported(self) -> list[str]:
        return sorted(self._registry.keys())

    def compute(
        self, name: str, series: Sequence[float] | pd.Series, **kwargs: object
    ) -> pd.Series:
        key = name.lower()
        if key not in self._registry:
            raise IndicatorError(f"Unsupported indicator: {name}")

        values = _to_numpy(series)
        output = self._registry[key](values, **kwargs)
        if isinstance(output, tuple):
            output = output[0]

        if len(output) != len(values):
            raise IndicatorError("Indicator output length does not match input length")

        if isinstance(series, pd.Series):
            return pd.Series(output, index=series.index, name=key)
        return pd.Series(output, name=key)

    def compute_ma(
        self,
        series: Sequence[float] | pd.Series,
        *,
        timeperiod: int = 20,
        matype: int = 0,
    ) -> pd.Series:
        values = _to_numpy(series)
        output = talib.MA(values, timeperiod=timeperiod, matype=matype)
        if len(output) != len(values):
            raise IndicatorError("Indicator output length does not match input length")
        if isinstance(series, pd.Series):
            return pd.Series(output, index=series.index, name="ma")
        return pd.Series(output, name="ma")

    def compute_macd(
        self,
        series: Sequence[float] | pd.Series,
        *,
        fastperiod: int = 12,
        slowperiod: int = 26,
        signalperiod: int = 9,
    ) -> pd.DataFrame:
        values = _to_numpy(series)
        macd, signal, hist = talib.MACD(
            values,
            fastperiod=fastperiod,
            slowperiod=slowperiod,
            signalperiod=signalperiod,
        )
        if len(macd) != len(values):
            raise IndicatorError("Indicator output length does not match input length")
        frame = pd.DataFrame(
            {
                "macd": macd,
                "signal": signal,
                "histogram": hist,
            }
        )
        if isinstance(series, pd.Series):
            frame.index = series.index
        return frame
