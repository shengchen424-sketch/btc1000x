"""EXP-001-INV: inverted EXP-001 trials on VALIDATION (diagnostic)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from exp001_baseline import grid, git_head, ms, gate  # noqa: E402

from b1k.backtest.engine import Backtester
from b1k.backtest.metrics import summarize, account_sim_one_lot
from b1k.config import PATHS, SPLITS
from b1k.data.store import load_1m, resample
from b1k.strategies.inverted import Inverted

EXP = "EXP-001-INV"
OUT = PATHS.results / EXP


def main() -> None:
    head = git_head()
    OUT.mkdir(parents=True, exist_ok=True)
    m = load_1m(start="2022-11-01", end=SPLITS.validation[1])
    fund = pd.read_parquet(PATHS.data_parquet / "BTCUSDT_funding.parquet")
    b15, b1h, b4h = resample(m, "15m"), resample(m, "1h"), resample(m, "4h")
    bt = Backtester(m, fund)
    v0, v1 = ms(SPLITS.validation[0]), ms(SPLITS.validation[1]) + 86_400_000
    rows, frames = [], []
    for inner in grid():
        strat = Inverted(inner)
        bars, htf = (b15, None) if strat.timeframe == "15m" else (b1h, b4h)
        tr = bt.run(strat, bars, htf, start_ms=v0, end_ms=v1)
        s = summarize(tr)
        s["trial_id"] = strat.trial_id
        s["gate"] = gate(s) if s["n"] else "FAIL"
        s["account_10usdt"] = account_sim_one_lot(tr) if len(tr) else None
        rows.append(s)
        if len(tr):
            frames.append(tr)
        print(strat.trial_id, "n", s["n"], "gross", round(s.get("mean_gross_r", float("nan")), 3),
              "net", round(s.get("mean_r", float("nan")), 3), s["gate"], flush=True)
    pd.DataFrame([{k: v for k, v in r.items() if not isinstance(v, dict)} for r in rows]).to_csv(OUT / "trials_val.csv", index=False)
    if frames:
        pd.concat(frames, ignore_index=True).to_parquet(OUT / "trades.parquet", index=False)
    verdict = {"experiment": EXP, "git_head": head, "run_at": datetime.now(timezone.utc).isoformat(),
               "candidates": [r["trial_id"] for r in rows if r["gate"] == "CANDIDATE"],
               "leads": [r["trial_id"] for r in rows if r["gate"] == "LEAD"], "val_rows": rows}
    (OUT / "verdict.json").write_text(json.dumps(verdict, indent=1, default=str))
    print(json.dumps({k: verdict[k] for k in ["candidates", "leads", "git_head"]}))


if __name__ == "__main__":
    main()
