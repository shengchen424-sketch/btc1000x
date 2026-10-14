"""Causal technical features. Every function uses only rows <= the current row.
Rolling windows are `closed='left'`-free by construction: the value at row i includes row i, which
is fine because a bar's features are consumed only after that bar has closed (see strategies.base)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def ema(x: pd.Series, n: int) -> pd.Series:
    return x.ewm(span=n, adjust=False, min_periods=n).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    pc = df["close"].shift(1)
    return pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return true_range(df).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def prior_swing_high(df: pd.DataFrame, n: int) -> pd.Series:
    """Highest high of the n bars strictly before the current bar."""
    return df["high"].shift(1).rolling(n, min_periods=n).max()


def prior_swing_low(df: pd.DataFrame, n: int) -> pd.Series:
    return df["low"].shift(1).rolling(n, min_periods=n).min()


def volume_ratio(df: pd.DataFrame, n: int = 20) -> pd.Series:
    """Current bar volume over the mean of the n prior bars."""
    return df["volume"] / df["volume"].shift(1).rolling(n, min_periods=n).mean()


def anchored_vwap(df: pd.DataFrame, anchor: pd.Series) -> pd.Series:
    """VWAP since the last bar where `anchor` is True (inclusive)."""
    grp = anchor.astype(int).cumsum()
    pv = (df["close"] * df["volume"]).groupby(grp).cumsum()
    v = df["volume"].groupby(grp).cumsum()
    return pv / v.replace(0, np.nan)


def ema_slope(x: pd.Series, n: int, lookback: int) -> pd.Series:
    """EMA change over `lookback` bars as a fraction of price."""
    e = ema(x, n)
    return (e - e.shift(lookback)) / x


def realized_vol(df: pd.DataFrame, n: int) -> pd.Series:
    r = np.log(df["close"]).diff()
    return r.rolling(n, min_periods=n).std()


def pct_rank(x: pd.Series, n: int) -> pd.Series:
    """Percentile of the current value within the last n values (inclusive), causal."""
    return x.rolling(n, min_periods=n).rank(pct=True)


def adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    up = df["high"].diff()
    dn = -df["low"].diff()
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = true_range(df)
    a = 1 / n
    atr_ = tr.ewm(alpha=a, adjust=False, min_periods=n).mean()
    pdi = 100 * pd.Series(plus, index=df.index).ewm(alpha=a, adjust=False, min_periods=n).mean() / atr_
    mdi = 100 * pd.Series(minus, index=df.index).ewm(alpha=a, adjust=False, min_periods=n).mean() / atr_
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=a, adjust=False, min_periods=n).mean()
