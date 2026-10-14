"""Strategy C — Funding-rate extreme (crowded-positioning reversal with carry).

Economic hypothesis: when the perpetual funding rate just settled is in the top tail of its trailing
distribution, longs are crowded and paying; the position is fragile and the carry favours the short.
Short after an extreme positive settlement; long after an extreme negative one. The position earns the
funding while held and bets on mean reversion of price and of the rate.

Signal clock: the 1h bar whose close_time is a settlement time (00:00, 08:00, 16:00 UTC). The rate
used is the one with funding_time == that close_time (known at that instant). Percentile is over the
trailing `window` settlements, causal. Entry at the next 1m open; fixed stop `stop_pct`; no target;
time exit after `hold_h` hours. No re-entry while a position is open (engine enforces).
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from b1k.features import ta
from .base import Strategy, SignalIntent, Direction


class FundingExtreme(Strategy):
    strategy_id = "FUNDING_EXTREME"
    version = "1.0"
    timeframe = "1h"
    htf = None

    def __init__(self, funding: pd.DataFrame, **params):
        super().__init__(**params)
        self.funding = funding.sort_values("funding_time").reset_index(drop=True)

    @classmethod
    def default_params(cls):
        return {"side": "SHORT", "pct": 0.97, "hold_h": 24, "stop_pct": 0.03, "window": 270}

    def prepare(self, bars: pd.DataFrame, htf_bars: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        p = self.params
        f = bars[["open_time", "close_time", "open", "high", "low", "close", "volume"]].copy()
        f["atr"] = ta.atr(bars, 14)
        fr = self.funding.rename(columns={"funding_time": "close_time", "funding_rate": "rate"})
        fr["pctile"] = fr["rate"].rolling(p["window"], min_periods=p["window"]).rank(pct=True)
        f = f.merge(fr[["close_time", "rate", "pctile"]], on="close_time", how="left")
        settle = f["rate"].notna() & f["pctile"].notna()
        if p["side"] == "SHORT":
            f["signal"] = settle & (f["pctile"] >= p["pct"]) & (f["rate"] > 0)
        else:
            f["signal"] = settle & (f["pctile"] <= 1 - p["pct"]) & (f["rate"] < 0)
        f["signal"] = f["signal"].fillna(False).astype(bool)
        return f

    def signal_at(self, feats: pd.DataFrame, i: int) -> Optional[SignalIntent]:
        row = feats.iloc[i]
        if not bool(row["signal"]):
            return None
        p = self.params
        close = float(row["close"])
        if p["side"] == "SHORT":
            d, stop = Direction.SHORT, close * (1 + p["stop_pct"])
        else:
            d, stop = Direction.LONG, close * (1 - p["stop_pct"])
        return SignalIntent(self.strategy_id, self.version, int(row["close_time"]), d, close, stop, stop, None,
                            int(p["hold_h"]), {"trial": self.trial_id},
                            {"rate": float(row["rate"]), "pctile": float(row["pctile"]), "atr": float(row["atr"])})
