"""Event-conditional fades (round 2 of Phase 2, from the literature scan in research/results/LIT-001.md).

ExpiryFade (EXP-005): Deribit options settle at 08:00 UTC on Fridays (monthly = last Friday). Dealer
hedging pushes price away from the settlement level into 08:00 and the move reverts after the hedge
unwinds (Weiss et al., FRL 2026). Signal: 15m bar closing at 08:00 UTC on an expiry day; move =
close(08:00)/close(07:00) - 1; if |move| >= min_move, fade it (SHORT after a rise, LONG after a fall).
Entry next 1m open, fixed stop, time exit after hold_bars x 15m.

ShockFade (EXP-006): a 1h bar whose absolute log return is >= k x trailing 30-day hourly sigma,
optionally with an open-interest drop >= oi_drop over the same hour (forced liquidations), is faded at
the next 1m open; fixed stop; time exit after hold_bars x 1h. OI comes from Binance 5m metrics; only
snapshots with open_time + 5m <= bar close_time are used (causal).
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from b1k.features import ta
from .base import Strategy, SignalIntent, Direction


def _is_last_friday(ts: pd.Timestamp) -> bool:
    return ts.weekday() == 4 and (ts + pd.Timedelta(days=7)).month != ts.month


class ExpiryFade(Strategy):
    strategy_id = "EXPIRY_FADE"
    version = "1.0"
    timeframe = "15m"

    @classmethod
    def default_params(cls):
        return {"events": "monthly", "min_move": 0.001, "stop_pct": 0.01, "hold_bars": 6}

    def prepare(self, bars: pd.DataFrame, htf_bars: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        p = self.params
        f = bars[["open_time", "close_time", "open", "high", "low", "close", "volume"]].copy()
        f["atr"] = ta.atr(bars, 14)
        ct = pd.to_datetime(f["close_time"], unit="ms", utc=True)
        at_0800 = (ct.dt.hour == 8) & (ct.dt.minute == 0)
        friday = ct.dt.weekday == 4
        if p["events"] == "monthly":
            ev = at_0800 & friday & ct.map(_is_last_friday)
        else:
            ev = at_0800 & friday
        f["move"] = f["close"] / f["close"].shift(4) - 1  # 07:00 -> 08:00 over four 15m bars
        f["event"] = ev
        f["signal"] = ev & (f["move"].abs() >= p["min_move"]) & f["atr"].notna()
        return f

    def signal_at(self, feats: pd.DataFrame, i: int) -> Optional[SignalIntent]:
        row = feats.iloc[i]
        if not bool(row["signal"]):
            return None
        p = self.params
        close, mv = float(row["close"]), float(row["move"])
        if mv > 0:
            d, stop = Direction.SHORT, close * (1 + p["stop_pct"])
        else:
            d, stop = Direction.LONG, close * (1 - p["stop_pct"])
        return SignalIntent(self.strategy_id, self.version, int(row["close_time"]), d, close, stop, stop, None,
                            int(p["hold_bars"]), {"trial": self.trial_id}, {"move": mv, "atr": float(row["atr"])})


class ShockFade(Strategy):
    strategy_id = "SHOCK_FADE"
    version = "1.0"
    timeframe = "1h"

    def __init__(self, metrics: Optional[pd.DataFrame] = None, **params):
        super().__init__(**params)
        self.metrics = None
        if metrics is not None:
            m = metrics[["open_time", "sum_open_interest"]].sort_values("open_time").copy()
            m["avail_time"] = m["open_time"] + 300_000  # a 5m snapshot is known at its close
            self.metrics = m

    @classmethod
    def default_params(cls):
        return {"k_sigma": 3.0, "oi_drop": 0.0, "stop_pct": 0.015, "hold_bars": 2, "sigma_window": 720}

    def prepare(self, bars: pd.DataFrame, htf_bars: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        p = self.params
        f = bars[["open_time", "close_time", "open", "high", "low", "close", "volume"]].copy()
        f["atr"] = ta.atr(bars, 14)
        r = np.log(f["close"]).diff()
        f["ret"] = r
        f["sigma"] = r.shift(1).rolling(p["sigma_window"], min_periods=p["sigma_window"]).std()
        f["shock"] = (r.abs() >= p["k_sigma"] * f["sigma"]) & f["sigma"].notna()
        if p["oi_drop"] > 0:
            if self.metrics is None:
                raise ValueError("oi_drop > 0 needs metrics")
            m = self.metrics
            end = pd.merge_asof(f[["close_time"]], m[["avail_time", "sum_open_interest"]], left_on="close_time",
                                right_on="avail_time", direction="backward")["sum_open_interest"]
            start = pd.merge_asof(f[["open_time"]], m[["avail_time", "sum_open_interest"]], left_on="open_time",
                                  right_on="avail_time", direction="backward")["sum_open_interest"]
            f["oi_chg"] = (end.to_numpy() / start.to_numpy() - 1)
            f["signal"] = f["shock"] & (f["oi_chg"] <= -p["oi_drop"])
        else:
            f["oi_chg"] = np.nan
            f["signal"] = f["shock"]
        f["signal"] = f["signal"].fillna(False).astype(bool) & f["atr"].notna()
        return f

    def signal_at(self, feats: pd.DataFrame, i: int) -> Optional[SignalIntent]:
        row = feats.iloc[i]
        if not bool(row["signal"]):
            return None
        p = self.params
        close, rt = float(row["close"]), float(row["ret"])
        if rt > 0:
            d, stop = Direction.SHORT, close * (1 + p["stop_pct"])
        else:
            d, stop = Direction.LONG, close * (1 - p["stop_pct"])
        return SignalIntent(self.strategy_id, self.version, int(row["close_time"]), d, close, stop, stop, None,
                            int(p["hold_bars"]), {"trial": self.trial_id},
                            {"ret": rt, "sigma": float(row["sigma"]), "oi_chg": float(row["oi_chg"]) if pd.notna(row["oi_chg"]) else float("nan")})
