"""Alternative daily data with explicit point-in-time rules.

Fear & Greed (alternative.me): value stamped at 00:00 UTC of day D is computed from the previous
day's inputs and published at that time; it is usable for a decision taken at D's close.
CoinMetrics community daily metrics: the row for day D is finalised after D ends (some metrics are
revised later). Rule here: the row for day D is usable only for decisions at the close of D+1 (one-day
lag), which is conservative for every column used.
"""
from __future__ import annotations

import pandas as pd

from b1k.config import PATHS


def load_fng() -> pd.DataFrame:
    p = PATHS.evidence / "alt" / "fng_2018-02_2026-10-14.parquet"
    d = pd.read_parquet(p).sort_values("open_time").reset_index(drop=True)
    d["avail_time"] = d["open_time"]  # known at 00:00 UTC of day D
    return d.rename(columns={"value": "fng"})


def load_coinmetrics() -> pd.DataFrame:
    p = PATHS.evidence / "alt" / "coinmetrics_btc_2019-06_2026-05-24.parquet"
    d = pd.read_parquet(p)
    d["open_time"] = (pd.to_datetime(d["time"], utc=True) - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(milliseconds=1)
    d["avail_time"] = d["open_time"] + 2 * 86_400_000  # row for D usable from the close of D+1 onward
    d["net_ex_inflow_usd"] = d["FlowInExUSD"] - d["FlowOutExUSD"]
    return d.sort_values("open_time").reset_index(drop=True)


def attach_daily(daily: pd.DataFrame, alt: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Attach alt columns to daily bars using only rows with avail_time <= bar close_time."""
    a = alt[["avail_time"] + cols].sort_values("avail_time")
    out = pd.merge_asof(daily[["close_time"]].sort_values("close_time"), a, left_on="close_time",
                        right_on="avail_time", direction="backward")
    out.index = daily.index
    return out[cols]
