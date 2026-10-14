import numpy as np
import pandas as pd

from b1k.data.store import resample
from b1k.strategies.orderflow import OrderFlowShock
from tests.conftest import make_1m


def test_orderflow_prepare_is_causal():
    m = make_1m(5 * 12000, seed=21, vol=0.001)
    rng = np.random.default_rng(2)
    m["count"] = rng.integers(50, 500, len(m))
    m["taker_buy_volume"] = m["volume"] * rng.uniform(0, 1, len(m))
    b = resample(m, "5m")
    s = OrderFlowShock(mode="REV", q_window_bars=2000, int_mult=1.2)
    full = s.prepare(b)
    k = 9000
    part = s.prepare(b.iloc[:k])
    for c in ["signal", "ofi", "int", "thr"]:
        a, b_ = part[c].iloc[-1], full[c].iloc[k - 1]
        assert (pd.isna(a) and pd.isna(b_)) or a == b_ or np.isclose(a, b_), (c, a, b_)
    assert full["signal"].sum() > 0
