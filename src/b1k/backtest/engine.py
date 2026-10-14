"""Event-driven backtester with 1-minute exit resolution.

Clock: a strategy signal is produced on the close of signal bar i (time = close_time_i). The entry is a
market order filled at the OPEN of the first 1m bar at or after close_time_i, plus entry slippage.
From then on each 1m bar is processed in order:
  1. trailing stop level is updated from PRIOR bars only (no same-bar look-ahead);
  2. stop-loss: long fills at min(stop, open) * (1 - slip_trigger) if low <= stop (gap -> open);
  3. take-profit: if high >= tp -> fill at tp (taker fee, trigger slippage). If stop and tp are
     both inside the same 1m bar the STOP is taken (conservative);
  4. time exit: at the first 1m bar whose open_time >= signal close_time + max_hold bars, at its open.
Funding is charged at every funding timestamp strictly after entry and <= exit, on the entry notional,
sign by direction (a long pays a positive rate). One position at a time.

Results are in R (1 R = planned loss = |entry_fill - stop| * qty) so that sizing is a separate step.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
import pandas as pd

from b1k.config import COSTS, CostModel
from b1k.data.store import RULE_MS
from b1k.strategies.base import Strategy, Direction, SignalIntent


@dataclass
class Trade:
    trial_id: str
    strategy_id: str
    direction: str
    signal_time: int
    entry_time: int
    exit_time: int
    entry_ref: float
    entry_fill: float
    stop: float
    take_profit: Optional[float]
    exit_fill: float
    exit_reason: str          # STOP | TP | TRAIL | TIME | END
    stop_frac: float          # planned loss as a fraction of entry
    gross_r: float
    fee_r: float
    slip_r: float
    funding_r: float
    net_r: float
    mfe_r: float
    mae_r: float
    minutes_held: int
    features: dict

    def to_row(self) -> dict:
        d = asdict(self)
        feats = d.pop("features")
        d.update({f"f_{k}": v for k, v in feats.items()})
        return d


class Backtester:
    def __init__(self, bars1m: pd.DataFrame, funding: Optional[pd.DataFrame], costs: CostModel = COSTS):
        self.m_open_time = bars1m["open_time"].to_numpy(np.int64)
        self.m_open = bars1m["open"].to_numpy(np.float64)
        self.m_high = bars1m["high"].to_numpy(np.float64)
        self.m_low = bars1m["low"].to_numpy(np.float64)
        self.m_close = bars1m["close"].to_numpy(np.float64)
        if funding is not None and len(funding):
            self.f_time = funding["funding_time"].to_numpy(np.int64)
            self.f_rate = funding["funding_rate"].to_numpy(np.float64)
        else:
            self.f_time = np.array([], dtype=np.int64)
            self.f_rate = np.array([], dtype=np.float64)
        self.costs = costs

    def run(self, strategy: Strategy, bars: pd.DataFrame, htf_bars: Optional[pd.DataFrame] = None,
            start_ms: Optional[int] = None, end_ms: Optional[int] = None) -> pd.DataFrame:
        """Signals are only taken for bars with close_time in [start_ms, end_ms); features are
        computed on the whole frame (warm-up may use earlier bars, which is causal)."""
        feats = strategy.prepare(bars, htf_bars)
        step = RULE_MS[strategy.timeframe]
        sig_idx = np.where(feats["signal"].to_numpy())[0]
        close_times = feats["close_time"].to_numpy(np.int64)
        trades: list[Trade] = []
        busy_until = -1
        for i in sig_idx:
            ct = close_times[i]
            if start_ms is not None and ct < start_ms:
                continue
            if end_ms is not None and ct >= end_ms:
                break
            if ct < busy_until:
                continue
            intent = strategy.signal_at(feats, i)
            if intent is None:
                continue
            t = self._simulate(intent, ct + intent.expected_holding_time * step, strategy)
            if t is None:
                continue
            trades.append(t)
            busy_until = t.exit_time
        if not trades:
            return pd.DataFrame()
        return pd.DataFrame([t.to_row() for t in trades])

    maker_limit_window_min: Optional[int] = None  # set by MakerBacktester

    def _entry(self, it: SignalIntent, j: int, s: float) -> Optional[tuple[int, float, float, float]]:
        """Returns (index of entry bar, entry fill, entry fee rate, entry slippage) or None if unfilled."""
        c = self.costs
        if self.maker_limit_window_min is None:
            return j, self.m_open[j] * (1 + s * c.slip_entry), c.taker_fee, c.slip_entry
        limit = it.entry
        end = min(j + self.maker_limit_window_min, len(self.m_open_time))
        for k in range(j, end):
            if (s > 0 and self.m_low[k] < limit) or (s < 0 and self.m_high[k] > limit):
                return k, limit, c.maker_fee, 0.0
        return None

    def _simulate(self, it: SignalIntent, time_exit_ms: int, strategy: Strategy) -> Optional[Trade]:
        c = self.costs
        j = int(np.searchsorted(self.m_open_time, it.signal_timestamp, side="left"))
        if j >= len(self.m_open_time) or self.m_open_time[j] - it.signal_timestamp > 5 * 60_000:
            return None  # no 1m bar to fill on (data gap): no trade
        long = it.direction == Direction.LONG
        s = 1.0 if long else -1.0
        ent = self._entry(it, j, s)
        if ent is None:
            return None  # passive order not filled inside its window
        j, entry_fill, entry_fee_rate, entry_slip = ent
        entry_time = int(self.m_open_time[j])
        stop = it.stop_loss
        if (long and stop >= entry_fill) or (not long and stop <= entry_fill):
            return None  # fill already beyond the stop: thesis void before entry
        risk_per_unit = abs(entry_fill - stop)
        trail_mult = it.confidence_metadata.get("trail_atr")
        atr0 = it.confidence_metadata.get("atr_at_signal")
        best = entry_fill
        mfe = 0.0
        mae = 0.0
        exit_fill = None
        reason = "END"
        k = j
        n = len(self.m_open_time)
        slip_exit = 0.0
        while k < n:
            ot = self.m_open_time[k]
            o, h, l = self.m_open[k], self.m_high[k], self.m_low[k]
            if ot >= time_exit_ms:
                exit_fill = o * (1 - s * c.slip_exit_time)
                slip_exit = c.slip_exit_time
                reason = "TIME"
                break
            # trailing stop from PRIOR bars
            eff_stop = stop
            if trail_mult is not None and k > j:
                tl = best - s * trail_mult * atr0
                if (long and tl > eff_stop) or (not long and tl < eff_stop):
                    eff_stop = tl
            hit_stop = (l <= eff_stop) if long else (h >= eff_stop)
            hit_tp = it.take_profit is not None and ((h >= it.take_profit) if long else (l <= it.take_profit))
            if hit_stop:
                level = min(eff_stop, o) if long else max(eff_stop, o)
                exit_fill = level * (1 - s * c.slip_exit_trigger)
                slip_exit = c.slip_exit_trigger
                reason = "STOP" if eff_stop == stop else "TRAIL"
                # excursion inside the exit bar counts up to the stop only
                mae = max(mae, s * (entry_fill - level) / risk_per_unit)
                break
            if hit_tp:
                exit_fill = it.take_profit * (1 - s * c.slip_exit_trigger)
                slip_exit = c.slip_exit_trigger
                reason = "TP"
                mfe = max(mfe, s * (it.take_profit - entry_fill) / risk_per_unit)
                break
            mfe = max(mfe, s * ((h if long else l) - entry_fill) / risk_per_unit)
            mae = max(mae, s * (entry_fill - (l if long else h)) / risk_per_unit)
            best = max(best, h) if long else min(best, l)
            k += 1
        if exit_fill is None:
            return None  # ran off the end of the data: open position is not a trade
        exit_time = int(self.m_open_time[k])
        gross = s * (exit_fill - entry_fill) / risk_per_unit
        fee = (entry_fee_rate * entry_fill + c.taker_fee * exit_fill) / risk_per_unit
        slip = (entry_slip * self.m_open[j] + slip_exit * (exit_fill / (1 - s * slip_exit))) / risk_per_unit
        # funding on entry notional for each settlement in (entry_time, exit_time]
        if len(self.f_time):
            a = np.searchsorted(self.f_time, entry_time, side="right")
            b = np.searchsorted(self.f_time, exit_time, side="right")
            funding = s * float(self.f_rate[a:b].sum()) * entry_fill / risk_per_unit
        else:
            funding = 0.0
        # gross already includes slippage through the fill prices; report slip separately for attribution
        net = gross - fee - funding
        return Trade(
            trial_id=strategy.trial_id, strategy_id=strategy.strategy_id, direction=it.direction.value,
            signal_time=it.signal_timestamp, entry_time=entry_time, exit_time=exit_time,
            entry_ref=it.entry, entry_fill=entry_fill, stop=stop, take_profit=it.take_profit,
            exit_fill=exit_fill, exit_reason=reason, stop_frac=risk_per_unit / entry_fill,
            gross_r=gross + slip, fee_r=fee, slip_r=slip, funding_r=funding, net_r=net,
            mfe_r=mfe, mae_r=mae, minutes_held=(exit_time - entry_time) // 60_000,
            features=it.supporting_features,
        )


class MakerBacktester(Backtester):
    """Passive limit entry at the signal close, cancelled after `window_min` minutes (EXP-010)."""

    def __init__(self, bars1m, funding, costs=COSTS, window_min: int = 60):
        super().__init__(bars1m, funding, costs)
        self.maker_limit_window_min = window_min
