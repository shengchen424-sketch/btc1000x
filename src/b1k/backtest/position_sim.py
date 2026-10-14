"""Daily-clock position simulator for always-in / long-flat / short-flat rules.

Position target in {-1, 0, +1} x size is decided on the daily close (00:00 UTC) and applied at the next
day's open. Daily net return = pos_prev * (open_{t+1}/open_t - 1) - |pos change| * (fee + slip)
- pos * funding settled during the day. Funding uses the realised 8h rates on the held notional.
Returns are fractions of equity at 1.0x notional per unit position.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from b1k.config import COSTS


def simulate(daily: pd.DataFrame, target: pd.Series, funding: pd.DataFrame,
             fee: float = COSTS.taker_fee, slip: float = COSTS.slip_entry) -> pd.DataFrame:
    """daily: resampled 1d bars (open_time, open, close, ...); target: position decided on each bar's
    close (index-aligned with daily). Executed at the next bar's open."""
    d = daily.reset_index(drop=True).copy()
    pos = target.shift(1).fillna(0.0).to_numpy()          # position held during bar t (decided at t-1 close)
    o = d["open"].to_numpy()
    nxt_open = np.r_[o[1:], d["close"].iloc[-1]]
    gross = pos * (nxt_open / o - 1)                       # open-to-open while holding pos
    chg = np.abs(np.diff(np.r_[0.0, pos]))
    cost = chg * (fee + slip)
    # funding settled inside [open_time, open_time + 1d)
    ft = funding["funding_time"].to_numpy(np.int64)
    fr = funding["funding_rate"].to_numpy()
    ot = d["open_time"].to_numpy(np.int64)
    idx0 = np.searchsorted(ft, ot, side="left")
    idx1 = np.searchsorted(ft, ot + 86_400_000, side="left")
    fsum = np.array([fr[a:b].sum() for a, b in zip(idx0, idx1)])
    fund = pos * fsum
    d["pos"] = pos
    d["ret_gross"] = gross
    d["ret_cost"] = cost
    d["ret_funding"] = fund
    d["ret_net"] = gross - cost - fund
    return d


def summarize_daily(sim: pd.DataFrame) -> dict:
    r = sim["ret_net"].to_numpy()
    if len(r) < 30:
        return {"days": int(len(r))}
    eq = np.cumprod(1 + r)
    dd = (np.maximum.accumulate(eq) - eq) / np.maximum.accumulate(eq)
    years = len(r) / 365.0
    cagr = eq[-1] ** (1 / years) - 1 if eq[-1] > 0 else -1.0
    t, p2 = stats.ttest_1samp(r, 0.0)
    ts = pd.to_datetime(sim["open_time"], unit="ms", utc=True)
    by_year = pd.Series(r).groupby(ts.dt.year.to_numpy()).apply(lambda x: float(np.prod(1 + x) - 1))
    active = sim["pos"] != 0
    return {
        "days": int(len(r)), "cagr": float(cagr), "total_return": float(eq[-1] - 1),
        "sharpe": float(r.mean() / r.std(ddof=1) * np.sqrt(365)) if r.std(ddof=1) > 0 else float("nan"),
        "t_stat": float(t), "p_one_sided": float(p2 / 2 if t > 0 else 1 - p2 / 2),
        "max_dd": float(dd.max()), "mar": float(cagr / dd.max()) if dd.max() > 0 else float("inf"),
        "time_in_market": float(active.mean()), "trades": int((np.abs(np.diff(np.r_[0.0, sim["pos"].to_numpy()])) > 0).sum()),
        "funding_total": float(sim["ret_funding"].sum()), "cost_total": float(sim["ret_cost"].sum()),
        "years_positive": int((by_year > 0).sum()), "years_total": int(len(by_year)),
        "by_year": {int(k): float(v) for k, v in by_year.items()},
    }
