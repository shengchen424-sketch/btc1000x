import numpy as np
import pandas as pd

from b1k.data.alt import attach_daily
from b1k.data.store import resample
from b1k.strategies.daily_alt import compression_breakout, fng_contrarian, exflow_zscore
from tests.conftest import make_1m


def test_compression_breakout_causal():
    m = make_1m(60 * 24 * 420, seed=12, vol=0.0007)
    d = resample(m, "1d")
    full = compression_breakout(d, q=0.3)
    part = compression_breakout(d.iloc[:300], q=0.3)
    assert (full.iloc[:300].to_numpy() == part.to_numpy()).all()


def test_attach_daily_respects_avail_time():
    m = make_1m(60 * 24 * 10)
    d = resample(m, "1d")
    alt = pd.DataFrame({"avail_time": d["close_time"] + 86_400_000, "x": np.arange(len(d), dtype=float)})
    out = attach_daily(d, alt, ["x"])
    # row i becomes available one day after bar i closes -> bar i sees row i-1 at most
    assert np.isnan(out["x"].iloc[0]) and out["x"].iloc[3] == 2.0


def test_fng_and_exflow_rules_hold_and_exit():
    m = make_1m(60 * 24 * 61)
    d = resample(m, "1d")
    n = len(d)
    f = pd.Series(([50] * 10 + [15] * 3 + [30] * 5 + [45] * 50)[:n], index=d.index, dtype=float)
    pos = fng_contrarian(d, f, lo=20, lo_exit=40, side="LONG")
    assert pos.iloc[10] == 1 and pos.iloc[17] == 1 and pos.iloc[18] == 0
    # z-score needs a window: use a short one for the test; a single spike at day 50 -> short for 5 days
    flow = pd.Series(np.r_[np.random.default_rng(0).normal(0, 1, 50), [1e9], np.zeros(n - 51)], index=d.index)
    pos2 = exflow_zscore(d, flow, z_thr=2.0, side="SHORT", hold=5, window=20)
    assert pos2.iloc[50] == -1 and pos2.iloc[54] == -1 and pos2.iloc[55] == 0
