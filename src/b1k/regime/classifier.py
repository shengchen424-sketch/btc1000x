"""Transparent regime baseline on 4h bars (RULE 7). Rules, no fitting; thresholds are percentiles
over a trailing 180-day window so the classifier is causal and self-scaling.

Labels: TREND_UP, TREND_DOWN, RANGE, VOLATILITY_EXPANSION, VOLATILITY_COMPRESSION, EVENT_RISK, UNKNOWN.
A 4h label is attached to a trade by the last 4h bar CLOSED at or before the signal time.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from b1k.features import ta

LABELS = ["TREND_UP", "TREND_DOWN", "RANGE", "VOLATILITY_EXPANSION", "VOLATILITY_COMPRESSION",
          "EVENT_RISK", "UNKNOWN"]
WIN = 180 * 6  # 180 days of 4h bars


def classify_4h(h: pd.DataFrame) -> pd.DataFrame:
    f = h[["open_time", "close_time", "close"]].copy()
    f["adx"] = ta.adx(h, 14)
    f["slope"] = ta.ema_slope(h["close"], 50, 6)
    f["rv"] = ta.realized_vol(h, 30)
    f["rv_pct"] = ta.pct_rank(f["rv"], WIN)
    f["atr_pct"] = ta.pct_rank(ta.atr(h, 14) / h["close"], WIN)
    bbw = h["close"].rolling(20).std() / h["close"].rolling(20).mean()
    f["bbw_pct"] = ta.pct_rank(bbw, WIN)
    f["ret1"] = np.log(h["close"]).diff().abs()
    f["shock"] = f["ret1"] > 4 * f["rv"].shift(1)
    lab = np.full(len(f), "UNKNOWN", dtype=object)
    ok = f["adx"].notna() & f["rv_pct"].notna() & f["bbw_pct"].notna()
    trend_up = ok & (f["adx"] > 25) & (f["slope"] > 0)
    trend_dn = ok & (f["adx"] > 25) & (f["slope"] < 0)
    expansion = ok & (f["rv_pct"] > 0.85)
    compression = ok & (f["bbw_pct"] < 0.15) & (f["rv_pct"] < 0.5)
    event = ok & f["shock"]
    lab[ok.to_numpy()] = "RANGE"
    lab[trend_up.to_numpy()] = "TREND_UP"
    lab[trend_dn.to_numpy()] = "TREND_DOWN"
    lab[compression.to_numpy()] = "VOLATILITY_COMPRESSION"
    lab[expansion.to_numpy()] = "VOLATILITY_EXPANSION"
    lab[event.to_numpy()] = "EVENT_RISK"
    f["regime"] = lab
    return f


def attach_regime(trades: pd.DataFrame, reg4h: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    r = reg4h[["close_time", "regime"]].sort_values("close_time")
    t = trades.sort_values("signal_time").copy()
    m = pd.merge_asof(t[["signal_time"]], r, left_on="signal_time", right_on="close_time",
                      direction="backward")
    t["regime"] = m["regime"].fillna("UNKNOWN").to_numpy()
    return t
