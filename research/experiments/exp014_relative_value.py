"""EXP-014: residual momentum and carry-adjusted momentum books on the same engine as the flow book."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp001_baseline import git_head  # noqa: E402
from st_audit_book import build_panel, signals, simulate, load_funding_daily, stats as bstats  # noqa: E402
from exp013_incremental import block_boot  # noqa: E402

from b1k.config import PATHS

OUT = PATHS.results / "EXP-014"
START, END = "2023-01-01", "2026-09-30"
IND = ("2025-01-01", "2026-09-30")
DEV = ("2023-01-01", "2024-12-31")


def residual_scores(px: pd.DataFrame, in_univ: pd.DataFrame, lookback: int) -> pd.DataFrame:
    r = np.log(px).diff()
    rb = r["BTCUSDT"]
    cov = r.rolling(90, min_periods=60).cov(rb)
    var = rb.rolling(90, min_periods=60).var()
    beta = cov.div(var, axis=0)
    resid = r - beta.mul(rb, axis=0)
    return resid.rolling(lookback, min_periods=lookback).sum().where(in_univ)


def run_book(px, score, funding):
    runs = []
    for off in range(7):
        d, _ = simulate(px, score, funding, START, END, offset=off)
        runs.append(d["net"])
    return pd.concat(runs, axis=1).mean(axis=1)


def window_stats(x: pd.Series, lo: str, hi: str) -> dict:
    x = x[lo:hi]
    t, p2 = stats.ttest_1samp(x.to_numpy(), 0.0)
    ci = block_boot(x.to_numpy())
    s = bstats(x); s["p_one_sided"] = float(p2 / 2 if t > 0 else 1 - p2 / 2)
    s["ci95_ann_pct"] = [round(365 * 100 * ci[0], 1), round(365 * 100 * ci[1], 1)]
    return s


def main():
    head = git_head()
    OUT.mkdir(parents=True, exist_ok=True)
    panel = build_panel()
    px, flow, in_univ = signals(panel)
    funding = load_funding_daily(px.index)
    f7 = (funding / 3).rolling(7, min_periods=3).mean().reindex(columns=px.columns).fillna(0.0)
    A = pd.read_parquet(PATHS.results / "EXP-013" / "daily_A.parquet")["A"]
    rm7, rm14 = residual_scores(px, in_univ, 7), residual_scores(px, in_univ, 14)
    books = {
        "RM7": rm7, "RM14": rm14,
        "CAM14": (rm14 - 21 * f7).where(in_univ),
        "CARRY_control": (-f7).where(in_univ),
    }
    results = {}
    for name, score in books.items():
        B = run_book(px, score, funding)
        B.rename(name).to_frame().to_parquet(OUT / f"daily_{name}.parquet")
        ind, dev = window_stats(B, *IND), window_stats(B, *DEV)
        corr = float(B[IND[0]:IND[1]].corr(A[IND[0]:IND[1]]))
        mix = 0.5 * A + 0.5 * B
        dmix = (mix - A)[IND[0]:IND[1]].to_numpy()
        ci = block_boot(dmix)
        mix_s = bstats(mix[IND[0]:IND[1]]); a_s = bstats(A[IND[0]:IND[1]])
        if name == "CARRY_control":
            gate = "CONTROL"
        elif ind["sharpe"] >= 0.7 and ind["p_one_sided"] < 0.0167 and dev["sharpe"] > 0 and corr < 0.3:
            gate = "INDEPENDENT-ALPHA"
        elif ind["sharpe"] >= 0.7 and ind["p_one_sided"] < 0.05 and corr < 0.3:
            gate = "LEAD"
        else:
            gate = "DISCARD"
        results[name] = {"independent_2025_26": ind, "dev_2023_24": dev, "corr_with_A": round(corr, 3),
                         "mix50_vs_A": {"A": a_s, "mix": mix_s, "ann_diff_pct": round(365 * 100 * dmix.mean(), 2),
                                        "ci95_ann_pct": [round(365 * 100 * ci[0], 1), round(365 * 100 * ci[1], 1)]},
                         "gate": gate}
        print(name, "| 2025-26", ind, "| 2023-24", {k: dev[k] for k in ["ann_pct", "sharpe"]}, "| corr A", round(corr, 2),
              "| mix50 sharpe", mix_s["sharpe"], "dd", mix_s["max_dd_pct"], "vs A", a_s["sharpe"], a_s["max_dd_pct"], "|", gate, flush=True)
    json.dump({"experiment": "EXP-014", "git_head": head, "results": results}, open(OUT / "verdict.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
