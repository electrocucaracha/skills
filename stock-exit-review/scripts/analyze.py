#!/usr/bin/env -S uv --quiet run --script
# Copyright (c) 2026
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Fetch or load adjusted daily OHLCV and emit reproducible market features."""

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1,<9",
#     "atomicwrites>=1.4,<2",
#     "numpy>=1.26,<3",
#     "pandas>=2.2,<3",
#     "ta==0.11.0",
#     "yfinance>=0.2.54,<1",
# ]
# ///

from __future__ import annotations

import datetime as dt
import json
import math
import re
from pathlib import Path

import click
from atomicwrites import atomic_write


def ticker_value(value: str) -> str:
    value = value.upper()
    if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=-]{0,31}", value):
        raise click.BadParameter("invalid provider ticker")
    return value


def ticker_option(ctx, param, value):
    return ticker_value(value) if value is not None else None


def read_json(path: str | Path) -> dict:
    path = Path(path)
    if path.stat().st_size > 5_000_000:
        raise ValueError("JSON input exceeds 5 MB")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("expected a JSON object")
    return data


def write_json(path: str | Path, data: dict, *, immutable: bool = False) -> bool:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
    try:
        with atomic_write(path, overwrite=not immutable, encoding="utf-8") as handle:
            handle.write(payload)
    except FileExistsError:
        if read_json(path) != data:
            raise ValueError("immutable record conflict: " + str(path)) from None
        return False
    return True


def load_prices(ticker: str, csv: str | None, as_of: dt.date):
    import numpy as np
    import pandas as pd

    if csv:
        if Path(csv).stat().st_size > 5_000_000:
            raise ValueError("CSV input exceeds 5 MB")
        frame = pd.read_csv(csv)
        frame.columns = frame.columns.str.lower()
        frame = frame.set_index("date")
    else:
        import yfinance as yf

        frame = yf.download(
            ticker,
            start=(as_of - dt.timedelta(days=800)).isoformat(),
            end=(as_of + dt.timedelta(days=1)).isoformat(),
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=30,
        )
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
        frame.columns = frame.columns.str.lower()
    if frame.empty:
        raise ValueError("no market data returned")
    dates = pd.to_datetime(frame.index, errors="raise")
    frame.index = pd.Index([date.date().isoformat() for date in dates])
    if frame.index.duplicated().any():
        raise ValueError("duplicate trading dates")
    frame = frame.loc[frame.index <= as_of.isoformat()].sort_index()
    frame = frame[["open", "high", "low", "close", "volume"]].apply(
        pd.to_numeric, errors="raise"
    )
    if len(frame) < 80 or not np.isfinite(frame.to_numpy()).all():
        raise ValueError("need at least 80 finite daily OHLCV rows")
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("prices must be positive")
    if (frame.volume < 0).any() or (
        (frame.high < frame[["open", "close", "low"]].max(axis=1))
        | (frame.low > frame[["open", "close", "high"]].min(axis=1))
    ).any():
        raise ValueError("invalid OHLCV relationships")
    return frame


def features(frame) -> dict:
    from ta.momentum import RSIIndicator
    from ta.trend import MACD, SMAIndicator
    from ta.volatility import AverageTrueRange

    close = frame.close
    returns = close.pct_change().dropna()
    fast = SMAIndicator(close, window=20).sma_indicator()
    slow = SMAIndicator(close, window=50).sma_indicator()
    atr = AverageTrueRange(frame.high, frame.low, close).average_true_range()
    values = {
        "close": close.iloc[-1],
        "sma_20": fast.iloc[-1],
        "sma_50": slow.iloc[-1],
        "rsi_14": RSIIndicator(close).rsi().iloc[-1],
        "macd_histogram": MACD(close).macd_diff().iloc[-1],
        "atr_fraction": atr.iloc[-1] / close.iloc[-1],
        "return_20": close.iloc[-1] / close.iloc[-21] - 1,
        "annualized_volatility": returns.tail(60).std() * math.sqrt(252),
        "max_drawdown": (close / close.cummax() - 1).min(),
        "drawdown_from_peak": close.iloc[-1] / close.max() - 1,
        "volume_ratio_20": (
            frame.volume.iloc[-1] / frame.volume.tail(20).mean()
            if frame.volume.tail(20).mean() > 0
            else None
        ),
    }
    return {
        key: round(float(value), 8) if value is not None else None
        for key, value in values.items()
    }


@click.command(help=__doc__)
@click.option("--ticker", callback=ticker_option, required=True)
@click.option(
    "--csv",
    type=click.Path(exists=True, dir_okay=False),
    help="adjusted daily OHLCV CSV",
)
@click.option("--benchmark", callback=ticker_option)
@click.option("--benchmark-csv", type=click.Path(exists=True, dir_okay=False))
@click.option("--as-of", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option(
    "--max-age-days", type=click.IntRange(0, 30), default=7, show_default=True
)
@click.option("--output", type=click.Path(dir_okay=False), required=True)
def main(ticker, csv, benchmark, benchmark_csv, as_of, max_age_days, output) -> None:
    today = dt.datetime.now(dt.UTC).date()
    as_of = as_of.date() if as_of else (today - dt.timedelta(days=1))
    if as_of > today:
        raise click.BadParameter("must not be future", param_hint="--as-of")
    if benchmark_csv and not benchmark:
        raise click.UsageError("benchmark-csv requires benchmark")
    frame = load_prices(ticker, csv, as_of)
    last_date = dt.date.fromisoformat(frame.index[-1])
    benchmark_ticker = benchmark
    benchmark = None
    warnings = ["technical-only; fundamentals and news not collected"]
    if benchmark_ticker:
        other = load_prices(benchmark_ticker, benchmark_csv, as_of)
        common = frame.index.intersection(other.index)
        if len(common) < 21 or other.index[-1] != frame.index[-1]:
            raise ValueError("benchmark dates do not cover the latest session")
        benchmark = {
            "ticker": benchmark_ticker,
            "source": "csv" if benchmark_csv else "yfinance",
            "return_20": float(
                other.loc[common[-1], "close"] / other.loc[common[-21], "close"] - 1
            ),
            "series": [
                {"date": date, "close": float(value)}
                for date, value in other.close.tail(500).items()
            ],
        }
    stale = (today - last_date).days > max_age_days
    if stale:
        warnings.append("stale prices; do not issue a hold/sale assessment")
    result = {
        "schema_version": 1,
        "ticker": ticker,
        "as_of": last_date.isoformat(),
        "requested_as_of": as_of.isoformat(),
        "captured_at": dt.datetime.now(dt.UTC).isoformat(),
        "source": "csv" if csv else "yfinance",
        "adjustment": "adjusted OHLC; provider may revise historical values",
        "features": features(frame),
        "benchmark": benchmark,
        "data_quality": {"usable": not stale, "warnings": warnings},
        "series": [
            {"date": date, "close": float(value)}
            for date, value in frame.close.tail(500).items()
        ],
    }
    write_json(output, result)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, ImportError) as error:
        raise SystemExit("analysis failed: " + str(error)) from None
