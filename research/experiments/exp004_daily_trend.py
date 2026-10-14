"""EXP-004 runner: daily-close trend rules on the perpetual (Strategy D, position-based)."""
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
from b1k.data.store import load_1m, resample
from b1k.strategies.daily_trend import RULES

EXP = "EXP-004"
OUT = PATHS.results / EXP
P_BONF = 0.05 / 6


def gate(s: dict, bh: dict, long_side: bool) -> str:
    if s.get("days", 0) < 300 or s["cagr"] <= 0 or s["years_positive"] < s["years_total"]:
        return "FAIL"
    cand = s["sharpe"] >= 1.0 and s["p_one_sided"] < P_BONF and s["mar"] >= 0.5
    if long_side and cand:
        cand = s["mar"] > bh["mar"]
    if cand:
        return "CANDIDATE"
    return "LEAD" if (s["sharpe"] >= 0.7 and s["p_one_sided"] < 0.05) else "FAIL"


def main() -> None:
    head = git_head()
    OUT.mkdir(parents=True, exist_ok=True)
    m = load_1m(start="2019-12-01", end=SPLITS.validation[1])
    fund = pd.read_parquet(PATHS.data_parquet / "BTCUSDT_funding.parquet")
    d = resample(m, "1d")
    v0, v1 = ms(SPLITS.validation[0]), ms(SPLITS.validation[1]) + 86_400_000
    t0, t1 = ms(SPLITS.train[0]), ms(SPLITS.train[1]) + 86_400_000
    results = {}
    bh_target = pd.Series(1.0, index=d.index)
    sims = {"BUY_HOLD": simulate(d, bh_target, fund)}
    for name, rule in RULES.items():
        sims[name] = simulate(d, rule(d), fund)
    for split, (a, b) in {"TRAIN": (t0, t1), "VAL": (v0, v1)}.items():
        results[split] = {}
        bh = summarize_daily(sims["BUY_HOLD"][(sims["BUY_HOLD"].open_time >= a) & (sims["BUY_HOLD"].open_time < b)])
        results[split]["BUY_HOLD"] = bh
        for name in RULES:
            s = sims[name]
            part = s[(s.open_time >= a) & (s.open_time < b)]
            r = summarize_daily(part)
            if split == "VAL":
                r["gate"] = gate(r, bh, name.endswith("_L"))
            results[split][name] = r
            print(split, name, {k: round(r[k], 3) for k in ["cagr", "sharpe", "max_dd", "mar", "p_one_sided", "funding_total", "time_in_market"]},
                  "trades", r["trades"], r.get("gate", ""), flush=True)
        print(split, "BUY_HOLD", {k: round(bh[k], 3) for k in ["cagr", "sharpe", "max_dd", "mar", "funding_total"]})
    pd.concat([s.assign(rule=n) for n, s in sims.items()]).to_parquet(OUT / "daily_sims.parquet", index=False)
    verdict = {"experiment": EXP, "git_head": head, "run_at": datetime.now(timezone.utc).isoformat(),
               "candidates": [n for n, r in results["VAL"].items() if r.get("gate") == "CANDIDATE"],
               "leads": [n for n, r in results["VAL"].items() if r.get("gate") == "LEAD"], "results": results}
    (OUT / "verdict.json").write_text(json.dumps(verdict, indent=1, default=str))
    print(json.dumps({k: verdict[k] for k in ["candidates", "leads", "git_head"]}))


if __name__ == "__main__":
    main()
