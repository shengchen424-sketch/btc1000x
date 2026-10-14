import numpy as np

from b1k.backtest.engine import MakerBacktester
from b1k.config import COSTS
from b1k.strategies.base import Direction
from tests.execution.test_engine import OneShot, _path, _bars15


def test_maker_entry_fills_only_when_price_trades_through_limit():
    p = [100.0] * 15 + [100.2] * 30 + [99.9] * 15 + [101.0] * 60   # dips below the limit (100) at minute 45
    m = _path(p)
    b = _bars15(m)
    ct = int(b["close_time"].iloc[0])
    s = OneShot(ct, Direction.LONG, stop=99.0, tp=None, hold=6)
    k = MakerBacktester(m, None, window_min=60).run(s, b)
    assert len(k) == 1
    assert k["entry_fill"].iloc[0] == 100.0 and k["entry_time"].iloc[0] == m["open_time"].iloc[45]
    assert np.isclose(k["slip_r"].iloc[0] - 0, (COSTS.slip_exit_time * k["exit_fill"].iloc[0] / (1 - COSTS.slip_exit_time)) / 1.0, atol=1e-6)


def test_maker_entry_unfilled_means_no_trade():
    p = [100.0] * 15 + [100.3] * 90
    m = _path(p)
    b = _bars15(m)
    s = OneShot(int(b["close_time"].iloc[0]), Direction.LONG, stop=99.0, tp=None, hold=4)
    k = MakerBacktester(m, None, window_min=60).run(s, b)
    assert len(k) == 0
