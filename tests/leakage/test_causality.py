"""No feature or signal may change when future bars are appended."""
import numpy as np
import pandas as pd
import pytest

from b1k.data.store import resample
from b1k.strategies import FailedBreak, TrendPullback
from b1k.strategies.base import align_htf, MarketState
from b1k.regime.classifier import classify_4h
from tests.conftest import make_1m

CHECK_COLS = ["signal", "atr", "level", "ext"]


@pytest.mark.parametrize("side", ["LONG", "SHORT"])
def test_failed_break_prepare_is_causal(side):
    m = make_1m(15 * 3000, seed=3, vol=0.0012)
    b = resample(m, "15m")
    s = FailedBreak(side=side, lookback=20, reclaim_bars=2)
    full = s.prepare(b)
    for k in [500, 1234, 2000, 2999]:
        part = s.prepare(b.iloc[:k])
        for c in CHECK_COLS:
            a, b_ = part[c].iloc[-1], full[c].iloc[k - 1]
            assert (pd.isna(a) and pd.isna(b_)) or a == b_ or np.isclose(a, b_), (c, k, a, b_)
    assert full["signal"].sum() > 0, "synthetic path produced no signals; test is vacuous"


@pytest.mark.parametrize("side", ["LONG", "SHORT"])
def test_trend_pullback_prepare_is_causal(side):
    m = make_1m(60 * 2400, seed=5, vol=0.0009, drift=1e-5 if side == "LONG" else -1e-5)
    b1h, b4h = resample(m, "1h"), resample(m, "4h")
    s = TrendPullback(side=side)
    full = s.prepare(b1h, b4h)
    for k in [700, 1500, 2399]:
        t = b1h["close_time"].iloc[k - 1]
        part = s.prepare(b1h.iloc[:k], b4h[b4h["close_time"] <= t])
        for c in ["signal", "atr", "h_slope", "pb_ext", "trend"]:
            a, b_ = part[c].iloc[-1], full[c].iloc[k - 1]
            assert (pd.isna(a) and pd.isna(b_)) or a == b_ or np.isclose(a, b_), (c, k, a, b_)


def test_align_htf_uses_only_closed_htf_bars():
    m = make_1m(60 * 50)
    b1h, b4h = resample(m, "1h"), resample(m, "4h")
    b4h = b4h.assign(x=np.arange(len(b4h), dtype=float))
    al = align_htf(b1h, b4h, ["x"])
    for i in range(len(b1h)):
        ct = b1h["close_time"].iloc[i]
        closed = b4h[b4h["close_time"] <= ct]
        if closed.empty:
            assert pd.isna(al["x"].iloc[i])
        else:
            assert al["x"].iloc[i] == closed["x"].iloc[-1]


def test_resample_drops_partial_bars_and_labels_close_time():
    m = make_1m(100)  # 100 minutes -> 6 full 15m bars, partial 7th dropped
    b = resample(m, "15m")
    assert len(b) == 6
    assert (b["close_time"] - b["open_time"] == 900_000).all()
    assert np.isclose(b["high"].iloc[0], m["high"].iloc[:15].max())


def test_generate_signal_rejects_lookahead_as_of():
    m = make_1m(15 * 300)
    b = resample(m, "15m")
    s = FailedBreak()
    with pytest.raises(ValueError):
        s.generate_signal(MarketState(bars=b, as_of_ms=int(b["close_time"].iloc[-1]) - 1))


def test_regime_classifier_is_causal():
    m = make_1m(240 * 1500, seed=9)
    h = resample(m, "4h")
    full = classify_4h(h)
    part = classify_4h(h.iloc[:1300])
    assert part["regime"].iloc[-1] == full["regime"].iloc[1299]
