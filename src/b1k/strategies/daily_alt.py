"""Daily position rules from compression (EXP-008) and sentiment / on-chain (EXP-009).

All decided on the daily close, executed at the next open (backtest/position_sim.py).

compression_breakout: Bollinger width (20-day std / 20-day mean) at or below its `q` quantile over
the trailing 100 days, then a close above the prior 20-day high -> long (mirror: below the prior
20-day low -> short). Exit on a close below the prior 10-day low (mirror above the 10-day high) or
after 20 days.

fng_contrarian: Fear & Greed <= lo -> long until F&G >= lo_exit or 30 days; F&G >= hi -> short until
F&G <= hi_exit or 30 days.

exflow_zscore: net exchange inflow (USD) z-score over 90 days; z >= 2 -> short 5 days (coins moving
to exchanges = sell pressure); z <= -2 -> long 5 days.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from b1k.features import ta


def compression_breakout(daily: pd.DataFrame, q: float = 0.10, side: str = "LONG", hold: int = 20) -> pd.Series:
    c = daily["close"]
    bbw = c.rolling(20).std() / c.rolling(20).mean()
    comp = ta.pct_rank(bbw, 100) <= q
    comp_recent = comp.shift(1).rolling(5, min_periods=1).max().astype(bool)  # compressed within the last 5 bars
    hi20 = c.shift(1).rolling(20).max()
    lo20 = c.shift(1).rolling(20).min()
    hi10 = c.shift(1).rolling(10).max()
    lo10 = c.shift(1).rolling(10).min()
    pos = np.zeros(len(c))
    p, age = 0.0, 0
    for i in range(len(c)):
        if np.isnan(hi20.iloc[i]) or np.isnan(bbw.iloc[i]):
            continue
        if p == 0:
            if side == "LONG" and comp_recent.iloc[i] and c.iloc[i] > hi20.iloc[i]:
                p, age = 1.0, 0
            elif side == "SHORT" and comp_recent.iloc[i] and c.iloc[i] < lo20.iloc[i]:
                p, age = -1.0, 0
        else:
            age += 1
            if (p == 1 and c.iloc[i] < lo10.iloc[i]) or (p == -1 and c.iloc[i] > hi10.iloc[i]) or age >= hold:
                p = 0.0
        pos[i] = p
    return pd.Series(pos, index=daily.index)


def fng_contrarian(daily: pd.DataFrame, fng: pd.Series, lo: int = 20, lo_exit: int = 40, hi: int = 80,
                   hi_exit: int = 60, side: str = "LONG", max_hold: int = 30) -> pd.Series:
    pos = np.zeros(len(daily))
    p, age = 0.0, 0
    for i in range(len(daily)):
        v = fng.iloc[i]
        if np.isnan(v):
            continue
        if p == 0:
            if side == "LONG" and v <= lo:
                p, age = 1.0, 0
            elif side == "SHORT" and v >= hi:
                p, age = -1.0, 0
        else:
            age += 1
            if (p == 1 and v >= lo_exit) or (p == -1 and v <= hi_exit) or age >= max_hold:
                p = 0.0
        pos[i] = p
    return pd.Series(pos, index=daily.index)


def exflow_zscore(daily: pd.DataFrame, net_inflow: pd.Series, z_thr: float = 2.0, side: str = "SHORT",
                  hold: int = 5, window: int = 90) -> pd.Series:
    z = (net_inflow - net_inflow.rolling(window).mean()) / net_inflow.rolling(window).std()
    pos = np.zeros(len(daily))
    p, age = 0.0, 0
    for i in range(len(daily)):
        v = z.iloc[i]
        if np.isnan(v):
            continue
        if p == 0:
            if side == "SHORT" and v >= z_thr:
                p, age = -1.0, 0
            elif side == "LONG" and v <= -z_thr:
                p, age = 1.0, 0
        else:
            age += 1
            if age >= hold:
                p = 0.0
        pos[i] = p
    return pd.Series(pos, index=daily.index)
