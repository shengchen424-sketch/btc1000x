"""Common strategy interface (RULE 2).

A strategy sees a MarketState: bars of its signal timeframe up to and including the LAST CLOSED bar,
plus optional higher-timeframe bars (also closed). It returns a SignalIntent or None. The intent is
advisory: the risk engine decides whether anything is executable.

Backtest and shadow share one code path: `prepare()` computes causal features for a whole frame
once, `signal_at(i)` reads row i. `generate_signal()` is `prepare()` + `signal_at(last)`.
tests/leakage checks that prepare(df[:k]).iloc[-1] == prepare(df).iloc[k-1].
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional

import pandas as pd


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True)
class SignalIntent:
    strategy_id: str
    strategy_version: str
    signal_timestamp: int            # ms, close time of the bar that produced the signal
    direction: Direction
    entry: float                     # reference price (last close); fill is the next open
    invalidation: float              # level whose breach voids the thesis (= stop basis)
    stop_loss: float
    take_profit: Optional[float]     # None -> exit by trailing / time rule only
    expected_holding_time: int       # bars of the signal timeframe
    confidence_metadata: dict[str, Any] = field(default_factory=dict)
    supporting_features: dict[str, float] = field(default_factory=dict)

    @property
    def stop_distance_frac(self) -> float:
        return abs(self.entry - self.stop_loss) / self.entry

    def to_dict(self) -> dict:
        d = asdict(self)
        d["direction"] = self.direction.value
        return d


@dataclass
class MarketState:
    bars: pd.DataFrame                   # signal timeframe, closed bars only, ascending
    htf_bars: Optional[pd.DataFrame] = None
    as_of_ms: int = 0                    # decision time; must be >= bars.close_time.iloc[-1]


class Strategy:
    strategy_id: str = "BASE"
    version: str = "0.0"
    timeframe: str = "15m"
    htf: Optional[str] = None
    params: dict[str, Any] = {}

    def __init__(self, **params: Any) -> None:
        self.params = {**self.default_params(), **params}

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return {}

    @property
    def trial_id(self) -> str:
        p = "_".join(f"{k}={v}" for k, v in sorted(self.params.items()))
        return f"{self.strategy_id}@{self.version}[{p}]"

    def prepare(self, bars: pd.DataFrame, htf_bars: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        raise NotImplementedError

    def signal_at(self, feats: pd.DataFrame, i: int) -> Optional[SignalIntent]:
        raise NotImplementedError

    def generate_signal(self, state: MarketState) -> Optional[SignalIntent]:
        if state.as_of_ms and state.as_of_ms < int(state.bars["close_time"].iloc[-1]):
            raise ValueError("MarketState.as_of_ms precedes the last bar's close: look-ahead")
        feats = self.prepare(state.bars, state.htf_bars)
        return self.signal_at(feats, len(feats) - 1)


def align_htf(bars: pd.DataFrame, htf_bars: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Attach HTF columns to each signal bar using only HTF bars that CLOSED at or before the
    signal bar's close_time (merge_asof on close_time, backward)."""
    h = htf_bars[["close_time"] + cols].sort_values("close_time")
    out = pd.merge_asof(bars[["close_time"]].sort_values("close_time"), h, on="close_time",
                        direction="backward")
    out.index = bars.index
    return out[cols]
