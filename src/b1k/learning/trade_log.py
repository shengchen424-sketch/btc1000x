"""Learning system (RULE 10): one record per simulated trade, plus a deterministic loss taxonomy.
Classification is rule-based and auditable. No rule is inferred from one trade: hypothesis
generation (intelligence/) only reads aggregates over >= 30 trades."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from b1k.config import PATHS

LOSS_CLASSES = ["NORMAL_STATISTICAL", "MODEL_FAILURE", "REGIME_MISMATCH", "EXECUTION_FAILURE",
                "RISK_RULE_VIOLATION", "DATA_QUALITY_FAILURE"]


def classify_loss(t: dict, eligible_regimes: set[str] | None = None) -> str | None:
    """t is a trade row (see backtest.engine.Trade.to_row plus 'regime'). Returns None for winners."""
    if t.get("net_r", 0) >= 0:
        return None
    if t.get("data_gap", False) or t.get("stale_data", False):
        return "DATA_QUALITY_FAILURE"
    if t.get("planned_loss_frac", 0) > 0.0101 or t.get("risk_rejected_but_filled", False):
        return "RISK_RULE_VIOLATION"
    # realised loss far beyond the planned 1R (gap, slippage): execution, not thesis
    if t.get("net_r", 0) < -1.5 and t.get("exit_reason") in ("STOP", "TRAIL"):
        return "EXECUTION_FAILURE"
    if eligible_regimes is not None and t.get("regime") not in eligible_regimes:
        return "REGIME_MISMATCH"
    # never moved in favour: the thesis was wrong at entry
    if t.get("mfe_r", 0) < 0.25 and t.get("exit_reason") == "STOP":
        return "MODEL_FAILURE"
    return "NORMAL_STATISTICAL"


def write_trade_log(trades: pd.DataFrame, experiment: str, path: Path | None = None) -> Path:
    path = path or (PATHS.results / experiment / "trades.parquet")
    path.parent.mkdir(parents=True, exist_ok=True)
    t = trades.copy()
    t["loss_class"] = [classify_loss(r) for r in t.to_dict("records")]
    t["logged_at"] = datetime.now(timezone.utc).isoformat()
    t.to_parquet(path, index=False)
    return path


def winners_profile(trades: pd.DataFrame, min_n: int = 30) -> dict:
    """Descriptive only: feature medians for winners vs losers when n allows. Used to GENERATE
    hypotheses for a new registration, never to change a running strategy."""
    if len(trades) < min_n:
        return {"n": int(len(trades)), "note": f"fewer than {min_n} trades: no profile"}
    feats = [c for c in trades.columns if c.startswith("f_")]
    w, l = trades[trades["net_r"] > 0], trades[trades["net_r"] <= 0]
    return {"n": int(len(trades)), "n_win": int(len(w)),
            "winner_medians": w[feats].median().to_dict(), "loser_medians": l[feats].median().to_dict(),
            "mfe_median_win": float(w["mfe_r"].median()), "mae_median_loss": float(l["mae_r"].median())}
