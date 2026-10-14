"""EXP-013: paired B - A tests of three incremental features on the reproduced flow book."""
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

from b1k.config import PATHS

OUT = PATHS.results / "EXP-013"
START, END = "2023-01-01", "2026-09-30"
IND = ("2025-01-01", "2026-09-30")
DEV = ("2023-01-01", "2024-12-31")


def block_boot(d: np.ndarray, n: int = 5000, B: int = 7, seed: int = 5):
    rng = np.random.default_rng(seed)
    blocks = [d[i:i + B] for i in range(0, len(d) - B + 1)]
    m = []
    for _ in range(n):
        idx = rng.integers(0, len(blocks), len(d) // B + 1)
        m.append(np.concatenate([blocks[i] for i in idx])[: len(d)].mean())
    return np.quantile(m, [0.025, 0.975])


def compare(a: pd.Series, b: pd.Series, lo: str, hi: str) -> dict:
    a, b = a[lo:hi], b[lo:hi]
    d = (b - a).to_numpy()
    ci = block_boot(d)
    t, p2 = stats.ttest_1samp(d, 0.0)
    return {"ann_diff_pct": round(365 * 100 * d.mean(), 2), "ci95_ann_pct": [round(365 * 100 * ci[0], 2), round(365 * 100 * ci[1], 2)],
            "p_one_sided": float(p2 / 2 if t > 0 else 1 - p2 / 2), "A": bstats(a), "B": bstats(b)}


def main():
    head = git_head()
    OUT.mkdir(parents=True, exist_ok=True)
    panel = build_panel()
    px, flow, _ = signals(panel)
    funding = load_funding_daily(px.index)
    btc = px["BTCUSDT"]; eth = px["ETHUSDT"]
    near_high = (btc >= 0.95 * btc.rolling(90).max())
    ethbtc_neg = ((eth / btc).pct_change(30) < 0)
    # funding 7-day mean per symbol (daily sums / 3 settlements)
    f7 = (funding / 3).rolling(7, min_periods=3).mean() if funding is not None else None
    feats = {
        "F1a_btc_nearhigh_long": dict(long_scale=near_high.map({True: 0.5, False: 1.0})),
        "F1b_btc_nearhigh_both": dict(long_scale=near_high.map({True: 0.5, False: 1.0}), short_scale=near_high.map({True: 0.5, False: 1.0})),
        "F2a_short_crowding": dict(exclude_short=(f7 < -0.0005)),
        "F2b_long_crowding": dict(exclude_long=(f7 > 0.0005)),
        "F3_ethbtc_long": dict(long_scale=ethbtc_neg.map({True: 0.5, False: 1.0})),
    }
    base = []
    for off in range(7):
        d, _ = simulate(px, flow, funding, START, END, offset=off); base.append(d["net"])
    A = pd.concat(base, axis=1).mean(axis=1)
    results = {}
    for name, kw in feats.items():
        runs = []
        for off in range(7):
            d, _ = simulate(px, flow, funding, START, END, offset=off, **kw); runs.append(d["net"])
        B = pd.concat(runs, axis=1).mean(axis=1)
        ind, dev = compare(A, B, *IND), compare(A, B, *DEV)
        same_sign = np.sign(ind["ann_diff_pct"]) == np.sign(dev["ann_diff_pct"])
        gate = "DISCARD"
        if ind["ann_diff_pct"] > 0 and ind["ci95_ann_pct"][0] > 0 and ind["p_one_sided"] < 0.01 and same_sign:
            gate = "ADOPT-CANDIDATE"
        elif ind["ann_diff_pct"] > 0 and ind["p_one_sided"] < 0.05 and same_sign:
            gate = "LEAD"
        results[name] = {"independent_2025_26": ind, "dev_2023_24": dev, "same_sign": bool(same_sign), "gate": gate}
        print(name, "| 2025-26 diff", ind["ann_diff_pct"], "CI", ind["ci95_ann_pct"], "p", round(ind["p_one_sided"], 4),
              "| 2023-24 diff", dev["ann_diff_pct"], "| B sharpe", ind["B"]["sharpe"], "dd", ind["B"]["max_dd_pct"], "| A sharpe", ind["A"]["sharpe"], "dd", ind["A"]["max_dd_pct"], "|", gate, flush=True)
        B.rename(name).to_frame().to_parquet(OUT / f"daily_{name}.parquet")
    A.rename("A").to_frame().to_parquet(OUT / "daily_A.parquet")
    json.dump({"experiment": "EXP-013", "git_head": head, "results": results}, open(OUT / "verdict.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
