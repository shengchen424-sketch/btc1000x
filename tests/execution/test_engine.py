"""Backtest engine fills on hand-built 1m paths."""
import numpy as np
import pandas as pd

from b1k.backtest.engine import Backtester
from b1k.backtest.metrics import summarize, account_sim_one_lot
from b1k.config import COSTS
from b1k.strategies.base import Strategy, SignalIntent, Direction


class OneShot(Strategy):
    """Fires one intent at a fixed bar; used to drive the engine deterministically."""
    strategy_id = "ONESHOT"
    version = "t"
    timeframe = "15m"

    def __init__(self, intent_at_close_ms, direction, stop, tp, hold=4, trail=None, atr=None):
        super().__init__()
        self.ct, self.d, self.stop, self.tp, self.hold, self.trail, self.atr = intent_at_close_ms, direction, stop, tp, hold, trail, atr

    def prepare(self, bars, htf_bars=None):
        f = bars[["open_time", "close_time", "close"]].copy()
        f["signal"] = f["close_time"] == self.ct
        return f

    def signal_at(self, feats, i):
        row = feats.iloc[i]
        meta = {}
        if self.trail is not None:
            meta = {"trail_atr": self.trail, "atr_at_signal": self.atr}
        return SignalIntent("ONESHOT", "t", int(row["close_time"]), self.d, float(row["close"]), self.stop,
                            self.stop, self.tp, self.hold, confidence_metadata=meta)


def _path(prices_1m, start=1_700_000_000_000 // 900_000 * 900_000):
    n = len(prices_1m)
    p = np.asarray(prices_1m, float)
    return pd.DataFrame({"open_time": start + 60_000 * np.arange(n), "open": p, "high": p + 0.05, "low": p - 0.05,
                         "close": p, "volume": 1.0, "quote_volume": 0.0, "count": 1, "taker_buy_volume": 0.0})


def _bars15(m):
    from b1k.data.store import resample
    return resample(m, "15m")


def test_stop_taken_before_tp_in_same_bar():
    m = _path([100.0] * 60)
    # bar at minute 30: huge range touching both stop (95) and tp (110)
    m.loc[30, ["high", "low"]] = [120.0, 90.0]
    b = _bars15(m)
    s = OneShot(int(b["close_time"].iloc[0]), Direction.LONG, stop=95.0, tp=110.0, hold=3)
    tr = Backtester(m, None).run(s, b)
    assert len(tr) == 1 and tr["exit_reason"].iloc[0] == "STOP"
    # fill at stop with trigger slippage, net about -1R minus fees
    assert tr["exit_fill"].iloc[0] < 95.0
    assert -1.3 < tr["net_r"].iloc[0] < -1.0


def test_gap_through_stop_fills_at_open():
    m = _path([100.0] * 60)
    m.loc[20:, ["open", "high", "low", "close"]] = [[80.0, 80.5, 79.5, 80.0]] * 40
    b = _bars15(m)
    s = OneShot(int(b["close_time"].iloc[0]), Direction.LONG, stop=95.0, tp=None, hold=3)
    tr = Backtester(m, None).run(s, b)
    assert tr["exit_reason"].iloc[0] == "STOP"
    assert np.isclose(tr["exit_fill"].iloc[0], 80.0 * (1 - COSTS.slip_exit_trigger))
    assert tr["net_r"].iloc[0] < -3.5  # the gap loss is real, not capped at -1R


def test_time_exit_and_funding_sign():
    m = _path([100.0] * 120)
    b = _bars15(m)
    ct = int(b["close_time"].iloc[0])
    fund = pd.DataFrame({"funding_time": [ct + 10 * 60_000], "funding_rate": [0.001]})
    bt = Backtester(m, fund)
    long = bt.run(OneShot(ct, Direction.LONG, stop=99.0, tp=None, hold=2), b)
    short = bt.run(OneShot(ct, Direction.SHORT, stop=101.0, tp=None, hold=2), b)
    assert long["exit_reason"].iloc[0] == "TIME" and long["exit_time"].iloc[0] == ct + 2 * 900_000
    assert long["funding_r"].iloc[0] > 0 and short["funding_r"].iloc[0] < 0  # long pays, short receives


def test_take_profit_fill():
    p = [100.0] * 30 + list(np.linspace(100, 104, 30))
    m = _path(p)
    b = _bars15(m)
    s = OneShot(int(b["close_time"].iloc[0]), Direction.LONG, stop=99.0, tp=102.0, hold=5)
    tr = Backtester(m, None).run(s, b)
    assert tr["exit_reason"].iloc[0] == "TP"
    assert 1.5 < tr["net_r"].iloc[0] < 2.1


def test_trailing_stop_uses_prior_bars_only():
    p = [100.0] * 15 + list(np.linspace(100, 110, 30)) + [104.0] * 30
    m = _path(p)
    b = _bars15(m)
    s = OneShot(int(b["close_time"].iloc[0]), Direction.LONG, stop=98.0, tp=None, hold=10, trail=1.0, atr=3.0)
    tr = Backtester(m, None).run(s, b)
    assert tr["exit_reason"].iloc[0] == "TRAIL"
    # best high before the drop is ~110 -> trail ~107; the drop bar opens at 104, so the fill is the open
    assert tr["exit_fill"].iloc[0] <= 104.0


def test_summary_and_account_sim_shapes():
    tr = pd.DataFrame({"net_r": [1.0, -1.0, 0.5], "gross_r": [1.1, -0.9, 0.6], "fee_r": [0.05] * 3,
                       "slip_r": [0.05] * 3, "funding_r": [0.0] * 3, "stop_frac": [0.005] * 3,
                       "minutes_held": [60, 30, 90], "exit_reason": ["TP", "STOP", "TIME"],
                       "entry_time": [1_700_000_000_000 + i * 86_400_000 for i in range(3)],
                       "entry_fill": [80_000.0] * 3})
    sm = summarize(tr)
    assert sm["n"] == 3 and np.isclose(sm["mean_r"], 1 / 6)
    acc = account_sim_one_lot(tr)
    assert acc["taken"] == 3 and acc["final_equity"] > 10.0
