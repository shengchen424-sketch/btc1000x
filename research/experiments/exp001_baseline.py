"""EXP-001 runner. Reads research/registrations/EXP-001.md's grid (hard-coded here identically),
runs TRAIN and VALIDATION, applies the registered gates, writes results. Refuses to run on a dirty
git tree so the commit reference is meaningful."""
from __future__ import annotations

import itertools
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from b1k.backtest.engine import Backtester
from b1k.backtest.metrics import summarize, account_sim_one_lot
from b1k.config import PATHS, SPLITS
from b1k.data.store import load_1m, resample, split_mask
from b1k.learning.trade_log import write_trade_log
from b1k.portfolio.router import learn_eligibility, route
from b1k.regime.classifier import classify_4h, attach_regime
from b1k.strategies import FailedBreak, TrendPullback

EXP = "EXP-001"
OUT = PATHS.results / EXP
N_TRIALS = 24
P_BONF = 0.05 / N_TRIALS


def grid():
    for side, lb, rr, vm in itertools.product(["LONG", "SHORT"], [48, 96], [1.5, 3.0], [0.0, 1.5]):
        yield FailedBreak(side=side, lookback=lb, rr=rr, vol_mult=vm)
    for side, pd_, tr in itertools.product(["LONG", "SHORT"], [0.5, 1.0], [2.0, 3.0]):
        yield TrendPullback(side=side, pb_depth=pd_, trail_atr=tr)


def git_head() -> str:
    root = PATHS.root
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True).stdout.strip()
    if dirty and "--allow-dirty" not in sys.argv:
        raise SystemExit("refusing to run on uncommitted code:\n" + dirty)
    return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def ms(d: str) -> int:
    return int(pd.Timestamp(d, tz="UTC").timestamp() * 1000)


def gate(s: dict) -> str:
    if s.get("n", 0) < 60 or not (s["mean_r"] > 0) or s["years_positive"] < s["years_total"]:
        return "FAIL"
    cand = (s["ci95_lo"] > 0 and s["p_one_sided"] < P_BONF and s["max_trade_share_of_profits"] <= 0.20
            and s["mean_stop_frac"] <= 0.0091)
    if cand:
        return "CANDIDATE"
    return "LEAD" if s["p_one_sided"] < 0.05 else "FAIL"


def main() -> None:
    head = git_head()
    OUT.mkdir(parents=True, exist_ok=True)
    m = load_1m(start="2019-12-01", end=SPLITS.validation[1])  # sealed holdout excluded by load_1m
    fund = pd.read_parquet(PATHS.data_parquet / "BTCUSDT_funding.parquet")
    b15, b1h, b4h = resample(m, "15m"), resample(m, "1h"), resample(m, "4h")
    reg = classify_4h(b4h)
    bt = Backtester(m, fund)
    t0, t1 = ms(SPLITS.train[0]), ms(SPLITS.train[1]) + 86_400_000
    v0, v1 = ms(SPLITS.validation[0]), ms(SPLITS.validation[1]) + 86_400_000
    rows_tr, rows_val, all_trades = [], [], []
    for strat in grid():
        bars, htf = (b15, None) if strat.timeframe == "15m" else (b1h, b4h)
        tr = bt.run(strat, bars, htf, start_ms=t0, end_ms=v1)
        tr = attach_regime(tr, reg) if len(tr) else tr
        if len(tr):
            tr["split"] = ["TRAIN" if x < t1 else "VAL" for x in tr["signal_time"]]
            all_trades.append(tr)
        for name, rows in (("TRAIN", rows_tr), ("VAL", rows_val)):
            part = tr[tr["split"] == name] if len(tr) else tr
            s = summarize(part)
            s["trial_id"] = strat.trial_id
            s["strategy"] = strat.strategy_id
            s["account_10usdt"] = account_sim_one_lot(part) if len(part) else None
            if name == "VAL":
                s["gate"] = gate(s) if s["n"] else "FAIL"
            rows.append(s)
        print(strat.trial_id, "TRAIN n", rows_tr[-1]["n"], "VAL n", rows_val[-1]["n"],
              "VAL mean", round(rows_val[-1].get("mean_r", float("nan")), 3), rows_val[-1]["gate"], flush=True)
    trades = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    write_trade_log(trades, EXP)
    flat = lambda rows: pd.DataFrame([{k: v for k, v in r.items() if not isinstance(v, dict)} for r in rows])
    flat(rows_tr).to_csv(OUT / "trials_train.csv", index=False)
    flat(rows_val).to_csv(OUT / "trials_val.csv", index=False)
    # router: eligibility on TRAIN, applied to VAL, against two baselines
    train_tr = trades[trades["split"] == "TRAIN"]
    val_tr = trades[trades["split"] == "VAL"]
    elig = learn_eligibility(train_tr)
    routed = route(val_tr, elig) if len(val_tr) else pd.DataFrame()
    pooled = summarize(val_tr)
    best_train = max(rows_tr, key=lambda r: r.get("mean_r", -9) if r["n"] >= 60 else -9)["trial_id"]
    best_single_val = summarize(val_tr[val_tr["trial_id"] == best_train])
    rs = summarize(routed)
    router_adds_value = bool(rs.get("n", 0) >= 60 and rs["mean_r"] > pooled.get("mean_r", -9)
                             and rs["mean_r"] > best_single_val.get("mean_r", -9))
    router = {"eligibility": elig.to_dict("records"), "routed_val": rs, "baseline_pooled_val": pooled,
              "baseline_best_train_trial": best_train, "baseline_best_trial_val": best_single_val,
              "router_adds_value": router_adds_value}
    (OUT / "router.json").write_text(json.dumps(router, indent=1, default=str))
    verdict = {
        "experiment": EXP, "git_head": head, "run_at": datetime.now(timezone.utc).isoformat(),
        "n_trials": len(rows_val), "candidates": [r["trial_id"] for r in rows_val if r["gate"] == "CANDIDATE"],
        "leads": [r["trial_id"] for r in rows_val if r["gate"] == "LEAD"],
        "router_adds_value": router_adds_value,
        "val_rows": rows_val, "train_rows": rows_tr,
    }
    (OUT / "verdict.json").write_text(json.dumps(verdict, indent=1, default=str))
    print(json.dumps({k: verdict[k] for k in ["candidates", "leads", "router_adds_value", "git_head"]}, indent=1))


if __name__ == "__main__":
    main()
