"""EXP-010: maker-entry execution study on Strategy B long (registered rescue attempt)."""
from __future__ import annotations

import itertools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp001_baseline import git_head, ms  # noqa: E402

from b1k.backtest.engine import Backtester, MakerBacktester
from b1k.backtest.metrics import summarize
from b1k.config import PATHS, SPLITS
from b1k.data.store import load_1m, resample
from b1k.strategies import TrendPullback

EXP = "EXP-010"
OUT = PATHS.results / EXP
P_BONF = 0.05 / 4


def gate(s: dict, adverse: float) -> str:
    if s.get("n", 0) < 60 or not (s["mean_r"] > 0) or s["years_positive"] < s["years_total"] or adverse > 0.1:
        return "FAIL"
    if s["p_one_sided"] < P_BONF and s["ci95_lo"] > 0:
        return "CANDIDATE"
    return "LEAD" if s["p_one_sided"] < 0.05 else "FAIL"


def main() -> None:
    head = git_head()
    OUT.mkdir(parents=True, exist_ok=True)
    m = load_1m(start="2019-12-01", end=SPLITS.validation[1])
    fund = pd.read_parquet(PATHS.data_parquet / "BTCUSDT_funding.parquet")
    b1h, b4h = resample(m, "1h"), resample(m, "4h")
    taker, maker = Backtester(m, fund), MakerBacktester(m, fund, window_min=60)
    v0, v1 = ms(SPLITS.validation[0]), ms(SPLITS.validation[1]) + 86_400_000
    rows = []
    for pd_, tr_ in itertools.product([0.5, 1.0], [2.0, 3.0]):
        strat = TrendPullback(side="LONG", pb_depth=pd_, trail_atr=tr_)
        t = taker.run(strat, b1h, b4h, start_ms=v0, end_ms=v1)
        k = maker.run(TrendPullback(side="LONG", pb_depth=pd_, trail_atr=tr_), b1h, b4h, start_ms=v0, end_ms=v1)
        filled = set(k["signal_time"]) if len(k) else set()
        t_filled = t[t["signal_time"].isin(filled)]
        t_unfilled = t[~t["signal_time"].isin(filled)]
        sm, st, sf, su = summarize(k), summarize(t), summarize(t_filled), summarize(t_unfilled)
        adverse = (su.get("mean_r", float("nan")) - sm.get("mean_r", float("nan"))) if su.get("n", 0) else 0.0
        row = {"trial_id": strat.trial_id, "signals_taker": st.get("n", 0), "filled": sm.get("n", 0),
               "fill_rate": sm.get("n", 0) / max(st.get("n", 1), 1),
               "maker_mean_r": sm.get("mean_r"), "maker_p": sm.get("p_one_sided"), "maker_ci_lo": sm.get("ci95_lo"),
               "maker_cost_r": sm.get("mean_cost_r"), "taker_mean_r_all": st.get("mean_r"),
               "taker_mean_r_same_signals": sf.get("mean_r"), "taker_mean_r_unfilled": su.get("mean_r"),
               "adverse_selection_r": adverse, "years_positive": sm.get("years_positive"), "by_year": sm.get("by_year"),
               "gate": gate(sm, adverse) if sm.get("n") else "FAIL"}
        rows.append(row)
        print({kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in row.items() if kk != "by_year"}, flush=True)
        if len(k):
            k.assign(model="maker").to_parquet(OUT / f"trades_maker_{pd_}_{tr_}.parquet", index=False)
    verdict = {"experiment": EXP, "git_head": head, "run_at": datetime.now(timezone.utc).isoformat(),
               "candidates": [r["trial_id"] for r in rows if r["gate"] == "CANDIDATE"],
               "leads": [r["trial_id"] for r in rows if r["gate"] == "LEAD"], "rows": rows}
    (OUT / "verdict.json").write_text(json.dumps(verdict, indent=1, default=str))
    print(json.dumps({k: verdict[k] for k in ["candidates", "leads", "git_head"]}))


if __name__ == "__main__":
    main()
