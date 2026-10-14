import numpy as np
import pandas as pd

from b1k.data.store import resample
from b1k.strategies.event_fade import ExpiryFade, ShockFade, _is_last_friday
from tests.conftest import make_1m


def test_last_friday_calendar():
    assert _is_last_friday(pd.Timestamp("2024-01-26", tz="UTC"))
    assert not _is_last_friday(pd.Timestamp("2024-01-19", tz="UTC"))
    assert not _is_last_friday(pd.Timestamp("2024-01-27", tz="UTC"))


def test_expiry_fade_events_and_causality():
    start = int(pd.Timestamp("2024-01-01", tz="UTC").timestamp() * 1000)
    m = make_1m(60 * 24 * 70, start_ms=start, seed=3, vol=0.002)
    b = resample(m, "15m")
    s = ExpiryFade(events="monthly", min_move=0.0)
    f = s.prepare(b)
    ev = f[f["event"]]
    ts = pd.to_datetime(ev["close_time"], unit="ms", utc=True)
    assert len(ev) == 2 and all(t.hour == 8 and t.weekday() == 4 for t in ts)  # Jan 26, Feb 23 2024
    k = int(ev.index[0]) + 1
    part = s.prepare(b.iloc[:k])
    assert part["signal"].iloc[-1] == f["signal"].iloc[k - 1] and np.isclose(part["move"].iloc[-1], f["move"].iloc[k - 1])


def test_shock_fade_oi_is_causal():
    m = make_1m(60 * 24 * 60, seed=7, vol=0.001)
    b = resample(m, "1h")
    ot = np.arange(m["open_time"].iloc[0], m["open_time"].iloc[-1], 300_000)
    rng = np.random.default_rng(1)
    metrics = pd.DataFrame({"open_time": ot, "sum_open_interest": 1e5 * np.exp(np.cumsum(rng.normal(0, 0.01, len(ot))))})
    s = ShockFade(metrics, oi_drop=0.02, k_sigma=1.0, sigma_window=200)
    f = s.prepare(b)
    k = 900
    t = b["close_time"].iloc[k - 1]
    part = s.prepare(b.iloc[:k])
    assert np.isclose(part["oi_chg"].iloc[-1], f["oi_chg"].iloc[k - 1]) and part["signal"].iloc[-1] == f["signal"].iloc[k - 1]
    # OI snapshot opened inside the last hour but closing after close_time must not be used
    m2 = metrics.copy()
    m2.loc[m2["open_time"] >= t - 299_999, "sum_open_interest"] = 1.0
    f2 = ShockFade(m2, oi_drop=0.02, k_sigma=1.0, sigma_window=200).prepare(b)
    assert np.isclose(f2["oi_chg"].iloc[k - 1], f["oi_chg"].iloc[k - 1])
