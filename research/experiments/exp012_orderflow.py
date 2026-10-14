"""EXP-012 runner: order-flow shocks, continuation vs reversal, 5m clock."""
from __future__ import annotations

import glob
import itertools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp001_baseline import git_head, ms  # noqa: E402

from b1k.backtest.engine import Backtester
from b1k.backtest.metrics import summarize, account_sim_one_lot
from b1k.config import PATHS, SPLITS
from b1k.data.store import load_1m, resample
from b1k.learning.trade_log import write_trade_log
from b1k.strategies.orderflow import OrderFlowShock

EXP = "EXP-012"
OUT = PATHS.results / EXP
P_BONF = 0.05 / 8


def gate(s: dict) -> str:
    if s.get("n", 0) < 60 or not (s["mean_r"] > 0) or s["years_positive"] < s["years_total"]:
        return "FAIL"
    if s["ci95_lo"] > 0 and s["p_one_sided"] < P_BONF and s["max_trade_share_of_profits"] <= 0.20:
        return "CANDIDATE"
    return "LEAD" if s["p_one_sided"] < 0.05 else "FAIL"


def main() -> None:
    head = git_head()
    OUT.mkdir(parents=True, exist_ok=True)
    m = load_1m(start="2021-05-01", end=SPLITS.validation[1])
    fund = pd.read_parquet(PATHS.data_parquet / "BTCUSDT_funding.parquet")
    b5 = resample(m, "5m")
    files = sorted(glob.glob(str(PATHS.data_parquet / "BTCUSDT_metrics_5m" / "*.parquet")))
    metrics = pd.concat([pd.read_parquet(f) for f in files]).drop_duplicates("open_time").sort_values("open_time")
    bt = Backtester(m, fund)
    t0, t1 = ms("2021-07-01"), ms(SPLITS.train[1]) + 86_400_000
    v1 = ms(SPLITS.validation[1]) + 86_400_000
    rows_tr, rows_val, frames = [], [], []
    for mode, hold, oi in itertools.product(["CONT", "REV"], [3, 12], [0.0, 0.005]):
        strat = OrderFlowShock(metrics, mode=mode, hold_bars=hold, oi_drop=oi)
        tr = bt.run(strat, b5, None, start_ms=t0, end_ms=v1)
        if len(tr):
            tr["split"] = ["TRAIN" if x < t1 else "VAL" for x in tr["signal_time"]]
            frames.append(tr)
        for name, rows in (("TRAIN", rows_tr), ("VAL", rows_val)):
            part = tr[tr["split"] == name] if len(tr) else tr
            s = summarize(part)
            s["trial_id"] = strat.trial_id
            s["account_10usdt"] = account_sim_one_lot(part) if len(part) else None
            if name == "VAL":
                s["gate"] = gate(s) if s["n"] else "FAIL"
            rows.append(s)
        print(mode, hold, oi, "TRAIN n", rows_tr[-1]["n"], "mean", round(rows_tr[-1].get("mean_r", float("nan")), 3),
              "| VAL n", rows_val[-1]["n"], "gross", round(rows_val[-1].get("mean_gross_r", float("nan")), 3),
              "net", round(rows_val[-1].get("mean_r", float("nan")), 3), "p", round(rows_val[-1].get("p_one_sided", float("nan")), 4),
              rows_val[-1]["gate"], flush=True)
    trades = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if len(trades):
        write_trade_log(trades, EXP)
    flat = lambda rows: pd.DataFrame([{k: v for k, v in r.items() if not isinstance(v, dict)} for r in rows])
    flat(rows_tr).to_csv(OUT / "trials_train.csv", index=False)
    flat(rows_val).to_csv(OUT / "trials_val.csv", index=False)
    verdict = {"experiment": EXP, "git_head": head, "run_at": datetime.now(timezone.utc).isoformat(),
               "candidates": [r["trial_id"] for r in rows_val if r["gate"] == "CANDIDATE"],
               "leads": [r["trial_id"] for r in rows_val if r["gate"] == "LEAD"], "val_rows": rows_val, "train_rows": rows_tr}
    (OUT / "verdict.json").write_text(json.dumps(verdict, indent=1, default=str))
    print(json.dumps({k: verdict[k] for k in ["candidates", "leads", "git_head"]}))


if __name__ == "__main__":
    main()
