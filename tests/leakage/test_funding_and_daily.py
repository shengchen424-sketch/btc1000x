import numpy as np
import pandas as pd

from b1k.backtest.position_sim import simulate
from b1k.data.store import resample
from b1k.strategies.daily_trend import t7, donchian
from b1k.strategies.funding_extreme import FundingExtreme
from tests.conftest import make_1m


def _funding_for(bars1h: pd.DataFrame, seed: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ct = bars1h["close_time"].to_numpy()
    st = ct[ct % 28_800_000 == 0]
    return pd.DataFrame({"funding_time": st, "funding_rate": rng.normal(1e-4, 3e-4, len(st))})


def test_funding_extreme_is_causal_and_uses_settled_rate():
    m = make_1m(60 * 24 * 150, seed=4)
    b1h = resample(m, "1h")
    fund = _funding_for(b1h)
    s = FundingExtreme(fund, side="SHORT", pct=0.9, window=60)
    full = s.prepare(b1h)
    assert full["signal"].sum() > 0
    k = 2500
    t = b1h["close_time"].iloc[k - 1]
    part = s.prepare(b1h.iloc[:k])
    assert part["signal"].iloc[-1] == full["signal"].iloc[k - 1]
    # the rate attached to a settlement bar is exactly the one settled at that close_time
    row = full[full["rate"].notna()].iloc[100]
    assert row["rate"] == fund.set_index("funding_time").loc[row["close_time"], "funding_rate"]
    # a future rate edit must not change earlier signals
    fund2 = fund.copy()
    fund2.loc[fund2["funding_time"] > t, "funding_rate"] = 0.01
    full2 = FundingExtreme(fund2, side="SHORT", pct=0.9, window=60).prepare(b1h)
    assert (full2["signal"].iloc[:k] == full["signal"].iloc[:k]).all()


def test_daily_rules_are_causal():
    m = make_1m(60 * 24 * 400, seed=6, drift=2e-6)
    d = resample(m, "1d")
    full = t7(d, n=50, entry=20, exit_=10)
    part = t7(d.iloc[:300], n=50, entry=20, exit_=10)
    assert (full.iloc[:300].to_numpy() == part.to_numpy()).all()
    full = donchian(d, entry=20, exit_=10, side="SHORT")
    part = donchian(d.iloc[:300], entry=20, exit_=10, side="SHORT")
    assert (full.iloc[:300].to_numpy() == part.to_numpy()).all()


def test_position_sim_applies_next_open_and_charges_changes():
    m = make_1m(60 * 24 * 10, seed=8)
    d = resample(m, "1d")
    target = pd.Series([0, 1, 1, 0, -1, -1, 0, 0, 0, 0][: len(d)], index=d.index, dtype=float)
    fund = pd.DataFrame({"funding_time": [], "funding_rate": []})
    sim = simulate(d, target, fund)
    assert sim["pos"].iloc[0] == 0 and sim["pos"].iloc[2] == 1 and sim["pos"].iloc[5] == -1
    o = d["open"].to_numpy()
    assert np.isclose(sim["ret_gross"].iloc[2], o[3] / o[2] - 1)
    assert sim["ret_cost"].iloc[2] > 0 and sim["ret_cost"].iloc[3] == 0  # entered during bar 2 (at its open)
