"""Strategy A — Failed breakdown / failed breakout (liquidity sweep and reclaim).

Economic hypothesis: a break of a well-watched prior swing level that is rejected quickly traps
breakout traders and triggers stops in the other direction; the reclaim is followed by a move back
through the range. Tested LONG (failed breakdown) and SHORT (failed breakout), mirrored.

Definition (long side, signal timeframe = 15m):
  level   = lowest low of the `lookback` bars before the sweep bar
  sweep   = bar whose low < level (break) and whose close is back above the level (reclaim) within
            the same bar, OR a bar that breaks and one of the next `reclaim_bars` bars closes above
            the level. The signal fires on the reclaim close.
  filter  = reclaim bar volume / mean(20 prior) >= vol_mult  (vol_mult = 0 disables)
  entry   = next bar open (market)
  stop    = sweep low - stop_atr * ATR14
  target  = entry + rr * (entry - stop)
  time    = max_hold bars after entry, exit at next open

Parameters are a small preregistered grid (research/registrations/EXP-001.md).
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from b1k.features import ta
from .base import Strategy, SignalIntent, Direction


class FailedBreak(Strategy):
    strategy_id = "FAILED_BREAK"
    version = "1.0"
    timeframe = "15m"

    @classmethod
    def default_params(cls):
        return {"side": "LONG", "lookback": 48, "reclaim_bars": 2, "stop_atr": 0.25,
                "rr": 2.0, "vol_mult": 0.0, "max_hold": 24}

    def prepare(self, bars: pd.DataFrame, htf_bars: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        p = self.params
        f = bars[["open_time", "close_time", "open", "high", "low", "close", "volume"]].copy()
        f["atr"] = ta.atr(bars, 14)
        f["volr"] = ta.volume_ratio(bars, 20)
        lb, rb = p["lookback"], p["reclaim_bars"]
        if p["side"] == "LONG":
            f["level"] = ta.prior_swing_low(bars, lb)
            broke = bars["low"] < f["level"]
            # level frozen at the first break bar; reclaim = close back above that level within rb bars
            f["brk_level"] = f["level"].where(broke)
            f["brk_low"] = bars["low"].where(broke)
            lvl = f["brk_level"].ffill(limit=rb)
            # extreme of the sweep: lowest low since the break, carried for rb bars
            ext = f["brk_low"].ffill(limit=rb)
            ext = pd.concat([ext, bars["low"].where(lvl.notna())], axis=1).min(axis=1).where(lvl.notna())
            f["signal"] = (bars["close"] > lvl) & lvl.notna()
            f["ext"] = ext
        else:
            f["level"] = ta.prior_swing_high(bars, lb)
            broke = bars["high"] > f["level"]
            f["brk_level"] = f["level"].where(broke)
            f["brk_high"] = bars["high"].where(broke)
            lvl = f["brk_level"].ffill(limit=rb)
            ext = f["brk_high"].ffill(limit=rb)
            ext = pd.concat([ext, bars["high"].where(lvl.notna())], axis=1).max(axis=1).where(lvl.notna())
            f["signal"] = (bars["close"] < lvl) & lvl.notna()
            f["ext"] = ext
        # only the FIRST reclaim after a break counts: suppress consecutive signals within rb bars
        sig = f["signal"].to_numpy().copy()
        last = -10**9
        for i in range(len(sig)):
            if sig[i]:
                if i - last <= rb:
                    sig[i] = False
                else:
                    last = i
        f["signal"] = sig & f["atr"].notna() & f["volr"].notna()
        if p["vol_mult"] > 0:
            f["signal"] &= f["volr"] >= p["vol_mult"]
        return f

    def signal_at(self, feats: pd.DataFrame, i: int) -> Optional[SignalIntent]:
        row = feats.iloc[i]
        if not bool(row["signal"]) or not np.isfinite(row["ext"]):
            return None
        p = self.params
        close, a = float(row["close"]), float(row["atr"])
        if p["side"] == "LONG":
            stop = float(row["ext"]) - p["stop_atr"] * a
            if stop >= close:
                return None
            tp = close + p["rr"] * (close - stop)
            d = Direction.LONG
        else:
            stop = float(row["ext"]) + p["stop_atr"] * a
            if stop <= close:
                return None
            tp = close - p["rr"] * (stop - close)
            d = Direction.SHORT
        return SignalIntent(
            strategy_id=self.strategy_id, strategy_version=self.version,
            signal_timestamp=int(row["close_time"]), direction=d, entry=close,
            invalidation=float(row["ext"]), stop_loss=stop, take_profit=tp,
            expected_holding_time=int(p["max_hold"]),
            confidence_metadata={"trial": self.trial_id},
            supporting_features={"level": float(row["level"]) if np.isfinite(row["level"]) else float("nan"),
                                 "atr": a, "volr": float(row["volr"])},
        )
