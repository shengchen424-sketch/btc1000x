"""Exact inversion of any strategy: same signal bars, opposite direction, stop and take-profit
mirrored around the entry reference, same holding time and trailing multiple. Used only as a
diagnostic (EXP-001-INV): if a strategy's loss is cost, its inverse loses too."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from .base import Strategy, SignalIntent, Direction


class Inverted(Strategy):
    version = "inv"

    def __init__(self, inner: Strategy) -> None:
        self.inner = inner
        self.strategy_id = f"INV_{inner.strategy_id}"
        self.timeframe = inner.timeframe
        self.htf = inner.htf
        self.params = inner.params

    @property
    def trial_id(self) -> str:
        return "INV:" + self.inner.trial_id

    def prepare(self, bars: pd.DataFrame, htf_bars: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        return self.inner.prepare(bars, htf_bars)

    def signal_at(self, feats: pd.DataFrame, i: int) -> Optional[SignalIntent]:
        it = self.inner.signal_at(feats, i)
        if it is None:
            return None
        e = it.entry
        d = Direction.SHORT if it.direction == Direction.LONG else Direction.LONG
        stop = 2 * e - it.stop_loss
        tp = None if it.take_profit is None else 2 * e - it.take_profit
        return SignalIntent(self.strategy_id, self.version, it.signal_timestamp, d, e, 2 * e - it.invalidation,
                            stop, tp, it.expected_holding_time, dict(it.confidence_metadata), dict(it.supporting_features))
