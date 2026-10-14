"""Strategy B — Trend pullback continuation.

Economic hypothesis: in an established higher-timeframe trend, a shallow pullback that resumes
in the trend direction offers a favourable location (stop below the pullback low) for a
continuation leg. Tested LONG and SHORT, mirrored.

Definition (long side, signal timeframe = 1h, HTF = 4h):
  trend    = 4h EMA50 slope over 6 bars > 0 AND 4h close > 4h EMA50 (only 4h bars closed by the
             1h bar's close_time are used)
  pullback = within the last `pb_window` 1h bars the low came within `pb_depth` ATR of EMA20(1h)
             (or below it) while the 1h close stayed above EMA50(1h)
  resume   = current 1h close > previous bar high (momentum resumes) AND close > EMA20
  entry    = next 1h open (market)
  stop     = min low of the pullback window - stop_atr * ATR14(1h)
  exit     = chandelier trail: highest high since entry - trail_atr * ATR (checked on 1m bars using
             the ATR at entry), or time exit after max_hold bars. No fixed take-profit.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from b1k.features import ta
from .base import Strategy, SignalIntent, Direction, align_htf


class TrendPullback(Strategy):
    strategy_id = "TREND_PULLBACK"
    version = "1.0"
    timeframe = "1h"
    htf = "4h"

    @classmethod
    def default_params(cls):
        return {"side": "LONG", "pb_depth": 0.5, "pb_window": 6, "stop_atr": 0.5,
                "trail_atr": 3.0, "max_hold": 48}

    def prepare(self, bars: pd.DataFrame, htf_bars: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        if htf_bars is None:
            raise ValueError("TrendPullback needs 4h bars")
        p = self.params
        f = bars[["open_time", "close_time", "open", "high", "low", "close", "volume"]].copy()
        f["atr"] = ta.atr(bars, 14)
        f["ema20"] = ta.ema(bars["close"], 20)
        f["ema50"] = ta.ema(bars["close"], 50)
        h = htf_bars.copy()
        h["h_ema50"] = ta.ema(h["close"], 50)
        h["h_slope"] = (h["h_ema50"] - h["h_ema50"].shift(6)) / h["close"]
        h["h_close"] = h["close"]
        hf = align_htf(bars, h, ["h_ema50", "h_slope", "h_close"])
        f = pd.concat([f, hf], axis=1)
        w = p["pb_window"]
        if p["side"] == "LONG":
            f["trend"] = (f["h_slope"] > 0) & (f["h_close"] > f["h_ema50"])
            touch = (bars["low"] - f["ema20"]) <= p["pb_depth"] * f["atr"]
            held = bars["close"] > f["ema50"]
            f["pulled"] = touch.rolling(w, min_periods=1).max().astype(bool) & held.rolling(w, min_periods=w).min().astype(bool)
            f["resume"] = (bars["close"] > bars["high"].shift(1)) & (bars["close"] > f["ema20"])
            f["pb_ext"] = bars["low"].rolling(w, min_periods=w).min()
        else:
            f["trend"] = (f["h_slope"] < 0) & (f["h_close"] < f["h_ema50"])
            touch = (f["ema20"] - bars["high"]) <= p["pb_depth"] * f["atr"]
            held = bars["close"] < f["ema50"]
            f["pulled"] = touch.rolling(w, min_periods=1).max().astype(bool) & held.rolling(w, min_periods=w).min().astype(bool)
            f["resume"] = (bars["close"] < bars["low"].shift(1)) & (bars["close"] < f["ema20"])
            f["pb_ext"] = bars["high"].rolling(w, min_periods=w).max()
        f["signal"] = f["trend"] & f["pulled"] & f["resume"] & f["atr"].notna() & f["h_slope"].notna()
        # one signal per pullback: suppress re-fires within pb_window bars
        sig = f["signal"].to_numpy().copy()
        last = -10**9
        for i in range(len(sig)):
            if sig[i]:
                if i - last <= w:
                    sig[i] = False
                else:
                    last = i
        f["signal"] = sig
        return f

    def signal_at(self, feats: pd.DataFrame, i: int) -> Optional[SignalIntent]:
        row = feats.iloc[i]
        if not bool(row["signal"]):
            return None
        p = self.params
        close, a = float(row["close"]), float(row["atr"])
        # initial stop = the tighter of the structural stop and the chandelier trail at entry,
        # so that 1 R is the loss actually possible on the first bar
        if p["side"] == "LONG":
            stop = max(float(row["pb_ext"]) - p["stop_atr"] * a, close - p["trail_atr"] * a)
            if stop >= close:
                return None
            d = Direction.LONG
        else:
            stop = min(float(row["pb_ext"]) + p["stop_atr"] * a, close + p["trail_atr"] * a)
            if stop <= close:
                return None
            d = Direction.SHORT
        return SignalIntent(
            strategy_id=self.strategy_id, strategy_version=self.version,
            signal_timestamp=int(row["close_time"]), direction=d, entry=close,
            invalidation=float(row["pb_ext"]), stop_loss=stop, take_profit=None,
            expected_holding_time=int(p["max_hold"]),
            confidence_metadata={"trial": self.trial_id, "trail_atr": p["trail_atr"], "atr_at_signal": a},
            supporting_features={"atr": a, "ema20": float(row["ema20"]), "h_slope": float(row["h_slope"])},
        )
