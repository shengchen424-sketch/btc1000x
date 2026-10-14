"""Strategy D — Daily-close trend rules on the perpetual, funding paid/received (position-based).

Rules decided on the daily close, executed at the next open (see backtest/position_sim.py).
  T7  : long when close > SMA(N) and close > prior 55-day high; exit on close < prior 20-day low or
        close < SMA(N). Short mirror: short when close < SMA(N) and close < prior 55-day low; cover on
        close > prior 20-day high or close > SMA(N).
  DON : Donchian 55/20 stop-and-reverse-free version: long on close > prior 55-day high, exit on close
        < prior 20-day low (and mirror).
  SMA : long while close > SMA(N), flat otherwise (and mirror short).
Each returns a target position series in {-1, 0, +1}.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _sma(x: pd.Series, n: int) -> pd.Series:
    return x.rolling(n, min_periods=n).mean()


def t7(daily: pd.DataFrame, n: int = 200, entry: int = 55, exit_: int = 20, side: str = "LONG") -> pd.Series:
    c = daily["close"]
    sma = _sma(c, n)
    hi = c.shift(1).rolling(entry, min_periods=entry).max()
    lo = c.shift(1).rolling(exit_, min_periods=exit_).min()
    lo_e = c.shift(1).rolling(entry, min_periods=entry).min()
    hi_x = c.shift(1).rolling(exit_, min_periods=exit_).max()
    pos = np.zeros(len(c))
    p = 0.0
    for i in range(len(c)):
        if np.isnan(sma.iloc[i]) or np.isnan(hi.iloc[i]):
            pos[i] = 0.0
            continue
        if side == "LONG":
            if p == 0 and c.iloc[i] > sma.iloc[i] and c.iloc[i] > hi.iloc[i]:
                p = 1.0
            elif p == 1 and (c.iloc[i] < lo.iloc[i] or c.iloc[i] < sma.iloc[i]):
                p = 0.0
        else:
            if p == 0 and c.iloc[i] < sma.iloc[i] and c.iloc[i] < lo_e.iloc[i]:
                p = -1.0
            elif p == -1 and (c.iloc[i] > hi_x.iloc[i] or c.iloc[i] > sma.iloc[i]):
                p = 0.0
        pos[i] = p
    return pd.Series(pos, index=daily.index)


def donchian(daily: pd.DataFrame, entry: int = 55, exit_: int = 20, side: str = "LONG") -> pd.Series:
    c = daily["close"]
    hi = c.shift(1).rolling(entry, min_periods=entry).max()
    lo = c.shift(1).rolling(exit_, min_periods=exit_).min()
    lo_e = c.shift(1).rolling(entry, min_periods=entry).min()
    hi_x = c.shift(1).rolling(exit_, min_periods=exit_).max()
    pos = np.zeros(len(c))
    p = 0.0
    for i in range(len(c)):
        if np.isnan(hi.iloc[i]):
            continue
        if side == "LONG":
            if p == 0 and c.iloc[i] > hi.iloc[i]:
                p = 1.0
            elif p == 1 and c.iloc[i] < lo.iloc[i]:
                p = 0.0
        else:
            if p == 0 and c.iloc[i] < lo_e.iloc[i]:
                p = -1.0
            elif p == -1 and c.iloc[i] > hi_x.iloc[i]:
                p = 0.0
        pos[i] = p
    return pd.Series(pos, index=daily.index)


def sma_filter(daily: pd.DataFrame, n: int = 200, side: str = "LONG") -> pd.Series:
    c = daily["close"]
    s = _sma(c, n)
    if side == "LONG":
        return ((c > s) & s.notna()).astype(float)
    return -((c < s) & s.notna()).astype(float)


RULES = {
    "T7_L": lambda d: t7(d, side="LONG"), "T7_S": lambda d: t7(d, side="SHORT"),
    "DON_L": lambda d: donchian(d, side="LONG"), "DON_S": lambda d: donchian(d, side="SHORT"),
    "SMA200_L": lambda d: sma_filter(d, side="LONG"), "SMA200_S": lambda d: sma_filter(d, side="SHORT"),
}
