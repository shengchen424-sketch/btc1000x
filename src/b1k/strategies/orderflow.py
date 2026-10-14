"""EXP-012 — order-flow shock (5m clock from 1m taker flow), continuation or reversal."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from b1k.features import ta
from .base import Strategy, SignalIntent, Direction


class OrderFlowShock(Strategy):
    strategy_id = "OFLOW_SHOCK"
    version = "1.0"
    timeframe = "5m"

    def __init__(self, metrics: Optional[pd.DataFrame] = None, **params):
        super().__init__(**params)
        self.metrics = None
        if metrics is not None:
            m = metrics[["open_time", "sum_open_interest"]].sort_values("open_time").copy()
            m["avail_time"] = m["open_time"] + 300_000
            self.metrics = m

    @classmethod
    def default_params(cls):
        return {"mode": "REV", "hold_bars": 3, "oi_drop": 0.0, "stop_pct": 0.006, "int_mult": 3.0,
                "q_window_bars": 8640, "q": 0.99}

    def prepare(self, bars: pd.DataFrame, htf_bars: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        p = self.params
        f = bars[["open_time", "close_time", "open", "high", "low", "close", "volume", "count", "taker_buy_volume"]].copy()
        f["atr"] = ta.atr(bars, 14)
        signed = 2 * f["taker_buy_volume"] - f["volume"]
        f["ofi"] = signed / f["volume"].replace(0, np.nan)
        f["int"] = f["count"] / f["count"].shift(1).rolling(2016, min_periods=500).median()  # 7 days of 5m bars
        thr = f["ofi"].abs().shift(1).rolling(p["q_window_bars"], min_periods=2000).quantile(p["q"])
        f["thr"] = thr
        sig = (f["ofi"].abs() >= thr) & (f["int"] >= p["int_mult"]) & thr.notna() & f["atr"].notna()
        if p["oi_drop"] > 0:
            if self.metrics is None:
                raise ValueError("oi_drop needs metrics")
            m = self.metrics
            end = pd.merge_asof(f[["close_time"]], m[["avail_time", "sum_open_interest"]], left_on="close_time",
                                right_on="avail_time", direction="backward")["sum_open_interest"].to_numpy()
            start = pd.merge_asof(f[["open_time"]], m[["avail_time", "sum_open_interest"]], left_on="open_time",
                                  right_on="avail_time", direction="backward")["sum_open_interest"].to_numpy()
            f["oi_chg"] = end / start - 1
            sig &= f["oi_chg"] <= -p["oi_drop"]
        else:
            f["oi_chg"] = np.nan
        f["signal"] = sig.fillna(False).astype(bool)
        return f

    def signal_at(self, feats: pd.DataFrame, i: int) -> Optional[SignalIntent]:
        row = feats.iloc[i]
        if not bool(row["signal"]):
            return None
        p = self.params
        close, ofi = float(row["close"]), float(row["ofi"])
        with_flow = ofi > 0
        long = with_flow if p["mode"] == "CONT" else not with_flow
        stop = close * (1 - p["stop_pct"]) if long else close * (1 + p["stop_pct"])
        return SignalIntent(self.strategy_id, self.version, int(row["close_time"]),
                            Direction.LONG if long else Direction.SHORT, close, stop, stop, None, int(p["hold_bars"]),
                            {"trial": self.trial_id}, {"ofi": ofi, "int": float(row["int"]), "atr": float(row["atr"]),
                                                       "oi_chg": float(row["oi_chg"]) if pd.notna(row["oi_chg"]) else float("nan")})
