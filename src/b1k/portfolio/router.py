"""Adaptive strategy router (RULE 7).

Eligibility is learned on TRAIN only: a (strategy trial, regime) pair is eligible when its TRAIN
trades in that regime number >= min_n and have mean net R > 0 with one-sided p < p_max. On VAL the
router takes a trial's trade only if its regime was eligible; otherwise NO_TRADE. The router must
beat two baselines on VAL to be worth its complexity: (a) every trial unfiltered, (b) each trial
alone. Expected utility = mean net R (costs included).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def learn_eligibility(train_trades: pd.DataFrame, min_n: int = 30, p_max: float = 0.10) -> pd.DataFrame:
    rows = []
    for (trial, reg), g in train_trades.groupby(["trial_id", "regime"]):
        r = g["net_r"].to_numpy()
        if len(r) >= 2:
            t, p2 = stats.ttest_1samp(r, 0.0)
            p1 = p2 / 2 if t > 0 else 1 - p2 / 2
        else:
            t, p1 = np.nan, np.nan
        rows.append({"trial_id": trial, "regime": reg, "n": len(r), "mean_r": r.mean(),
                     "p_one_sided": p1,
                     "eligible": bool(len(r) >= min_n and r.mean() > 0 and p1 < p_max)})
    return pd.DataFrame(rows)


def route(trades: pd.DataFrame, eligibility: pd.DataFrame) -> pd.DataFrame:
    """Keep only trades whose (trial, regime) is eligible; resolve overlaps by earliest signal
    (one position at a time)."""
    el = eligibility[eligibility["eligible"]][["trial_id", "regime"]]
    kept = trades.merge(el, on=["trial_id", "regime"], how="inner").sort_values("signal_time")
    out, busy = [], -1
    for _, t in kept.iterrows():
        if t["signal_time"] < busy:
            continue
        out.append(t)
        busy = t["exit_time"]
    return pd.DataFrame(out)
