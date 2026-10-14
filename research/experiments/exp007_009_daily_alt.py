"""EXP-007 (FOMC), EXP-008 (compression breakout), EXP-009 (sentiment / on-chain) — daily position sims.
Usage: python exp007_009_daily_alt.py 007|008|009"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp001_baseline import git_head, ms  # noqa: E402

from b1k.backtest.position_sim import simulate, summarize_daily
from b1k.config import PATHS, SPLITS
from b1k.data.alt import load_fng, load_coinmetrics, attach_daily
from b1k.data.store import load_1m, resample
from b1k.strategies.daily_alt import compression_breakout, fng_contrarian, exflow_zscore
from b1k.strategies.fomc import fomc_positions


def gate(s: dict, bh: dict, long_side: bool, p_bonf: float) -> str:
    if s.get("days", 0) < 300 or s["cagr"] <= 0 or s["years_positive"] < s["years_total"]:
        return "FAIL"
    cand = s["sharpe"] >= 1.0 and s["p_one_sided"] < p_bonf and s["mar"] >= 0.5
    if long_side and cand:
        cand = s["mar"] > bh["mar"]
    if cand:
        return "CANDIDATE"
    return "LEAD" if (s["sharpe"] >= 0.7 and s["p_one_sided"] < 0.05) else "FAIL"


def trials_for(exp: str, d: pd.DataFrame) -> dict[str, tuple[pd.Series, bool]]:
    if exp == "EXP-007":
        return {m: (fomc_positions(d, m), m != "DAY_SHORT") for m in ["PRE_LONG", "DAY_SHORT", "BOTH"]}
    if exp == "EXP-008":
        return {f"CB_q{q}_{s}": (compression_breakout(d, q=q, side=s), s == "LONG")
                for q in [0.10, 0.20] for s in ["LONG", "SHORT"]}
    fng = attach_daily(d, load_fng(), ["fng"])["fng"]
    cm = attach_daily(d, load_coinmetrics(), ["net_ex_inflow_usd"])["net_ex_inflow_usd"]
    return {
        "FNG_L": (fng_contrarian(d, fng, lo=20, lo_exit=40, side="LONG"), True),
        "FNG_L25": (fng_contrarian(d, fng, lo=25, lo_exit=50, side="LONG"), True),
        "FNG_S": (fng_contrarian(d, fng, hi=80, hi_exit=60, side="SHORT"), False),
        "FNG_S75": (fng_contrarian(d, fng, hi=75, hi_exit=50, side="SHORT"), False),
        "EXFLOW_S": (exflow_zscore(d, cm, z_thr=2.0, side="SHORT"), False),
        "EXFLOW_L": (exflow_zscore(d, cm, z_thr=2.0, side="LONG"), True),
    }


def main(exp: str) -> None:
    head = git_head()
    out = PATHS.results / exp
    out.mkdir(parents=True, exist_ok=True)
    m = load_1m(start="2019-12-01", end=SPLITS.validation[1])
    fund = pd.read_parquet(PATHS.data_parquet / "BTCUSDT_funding.parquet")
    d = resample(m, "1d")
    trials = trials_for(exp, d)
    p_bonf = 0.05 / len(trials)
    sims = {"BUY_HOLD": simulate(d, pd.Series(1.0, index=d.index), fund)}
    for name, (target, _) in trials.items():
        sims[name] = simulate(d, target, fund)
    windows = {"TRAIN": (ms(SPLITS.train[0]), ms(SPLITS.train[1]) + 86_400_000),
               "VAL": (ms(SPLITS.validation[0]), ms(SPLITS.validation[1]) + 86_400_000)}
    results = {}
    for split, (a, b) in windows.items():
        results[split] = {}
        bh = summarize_daily(sims["BUY_HOLD"][(sims["BUY_HOLD"].open_time >= a) & (sims["BUY_HOLD"].open_time < b)])
        results[split]["BUY_HOLD"] = bh
        for name, (_, long_side) in trials.items():
            s = sims[name]
            r = summarize_daily(s[(s.open_time >= a) & (s.open_time < b)])
            if split == "VAL":
                r["gate"] = gate(r, bh, long_side, p_bonf)
            results[split][name] = r
            print(split, name, {k: round(r[k], 3) for k in ["cagr", "sharpe", "max_dd", "mar", "p_one_sided", "time_in_market"]},
                  "trades", r["trades"], r.get("gate", ""), flush=True)
        print(split, "BUY_HOLD", {k: round(bh[k], 3) for k in ["cagr", "sharpe", "max_dd", "mar"]})
    pd.concat([s.assign(rule=n) for n, s in sims.items()]).to_parquet(out / "daily_sims.parquet", index=False)
    verdict = {"experiment": exp, "git_head": head, "run_at": datetime.now(timezone.utc).isoformat(),
               "candidates": [n for n, r in results["VAL"].items() if r.get("gate") == "CANDIDATE"],
               "leads": [n for n, r in results["VAL"].items() if r.get("gate") == "LEAD"], "results": results}
    (out / "verdict.json").write_text(json.dumps(verdict, indent=1, default=str))
    print(json.dumps({k: verdict[k] for k in ["candidates", "leads", "git_head"]}))


if __name__ == "__main__":
    main({"007": "EXP-007", "008": "EXP-008", "009": "EXP-009"}[sys.argv[1]])
