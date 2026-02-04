from __future__ import annotations

import pandas as pd

from services.market_service import (
    build_macd_points,
    build_ma_points,
    build_rsi_points,
)


def test_build_rsi_points_rounds_to_three_decimals() -> None:
    timestamps = pd.Series([pd.Timestamp("2024-01-01")])
    values = pd.Series([50.12345])

    points = build_rsi_points(timestamps, values)

    assert points[0].rsi == 50.123


def test_build_ma_points_rounds_to_three_decimals() -> None:
    timestamps = pd.Series([pd.Timestamp("2024-01-01")])
    values = pd.Series([10.98765])

    points = build_ma_points(timestamps, values)

    assert points[0].ma == 10.988


def test_build_macd_points_rounds_to_three_decimals() -> None:
    timestamps = pd.Series([pd.Timestamp("2024-01-01")])
    values = pd.DataFrame(
        {
            "macd": [1.23456],
            "signal": [2.34567],
            "histogram": [3.45678],
        }
    )

    points = build_macd_points(timestamps, values)

    assert points[0].macd == 1.235
    assert points[0].signal == 2.346
    assert points[0].histogram == 3.457
