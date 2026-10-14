"""Trade-level statistics in R, with uncertainty. Nothing here is a verdict; gates live in the
experiment registration."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def bootstrap_ci(x: np.ndarray, n_boot: int = 10_000, alpha: float = 0.05, seed: int = 7) -> tuple[float, float]:
    if len(x) < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    means = x[idx].mean(axis=1)
    return (float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2)))


def summarize(trades: pd.DataFrame) -> dict:
    if trades is None or trades.empty:
        return {"n": 0}
    r = trades["net_r"].to_numpy(np.float64)
    gross_pos = r[r > 0].sum()
    gross_neg = -r[r < 0].sum()
    t, p_two = stats.ttest_1samp(r, 0.0) if len(r) > 1 else (float("nan"), float("nan"))
    p_one = p_two / 2 if np.isfinite(t) and t > 0 else (1 - p_two / 2 if np.isfinite(t) else float("nan"))
    lo, hi = bootstrap_ci(r)
    eq = np.cumsum(r)
    dd = float((np.maximum.accumulate(eq) - eq).max()) if len(eq) else 0.0
    years = pd.to_datetime(trades["entry_time"], unit="ms", utc=True).dt.year
    by_year = trades.groupby(years)["net_r"].agg(["count", "mean", "sum"])
    return {
        "n": int(len(r)),
        "mean_r": float(r.mean()),
        "median_r": float(np.median(r)),
        "std_r": float(r.std(ddof=1)) if len(r) > 1 else float("nan"),
        "win_rate": float((r > 0).mean()),
        "t_stat": float(t),
        "p_one_sided": float(p_one),
        "ci95_lo": lo, "ci95_hi": hi,
        "sum_r": float(r.sum()),
        "profit_factor": float(gross_pos / gross_neg) if gross_neg > 0 else float("inf"),
        "max_dd_r": dd,
        "max_trade_share_of_profits": float(r.max() / gross_pos) if gross_pos > 0 else float("nan"),
        "mean_gross_r": float(trades["gross_r"].mean()),
        "mean_cost_r": float((trades["fee_r"] + trades["slip_r"] + trades["funding_r"]).mean()),
        "mean_fee_r": float(trades["fee_r"].mean()),
        "mean_funding_r": float(trades["funding_r"].mean()),
        "mean_stop_frac": float(trades["stop_frac"].mean()),
        "median_minutes_held": float(trades["minutes_held"].median()),
        "exit_reasons": trades["exit_reason"].value_counts().to_dict(),
        "years_positive": int((by_year["sum"] > 0).sum()),
        "years_total": int(len(by_year)),
        "by_year": {int(y): {"n": int(c), "mean_r": float(m), "sum_r": float(s_)}
                    for y, (c, m, s_) in by_year.iterrows()},
    }


def account_sim_one_lot(trades: pd.DataFrame, equity0: float = 10.0, risk_frac: float = 0.01,
                        lot_btc: float = 0.0001, taker: float = 0.0006) -> dict:
    """What the 10 USDT account can actually do: every trade is exactly one lot (0.0001 BTC) or
    nothing. A trade is skipped when one lot's planned loss (stop + round-trip fee) exceeds
    risk_frac * equity. Equity compounds; lots scale with floor(equity * risk / one-lot risk)."""
    if trades is None or trades.empty:
        return {"final_equity": equity0, "taken": 0, "skipped_risk": 0}
    eq = equity0
    taken = skipped = 0
    peak, maxdd = eq, 0.0
    for _, t in trades.sort_values("entry_time").iterrows():
        notional = lot_btc * t["entry_fill"]
        one_lot_risk = notional * (t["stop_frac"] + 2 * taker)
        budget = eq * risk_frac
        lots = int(budget // one_lot_risk)
        if lots < 1:
            skipped += 1
            continue
        pnl = lots * notional * t["stop_frac"] * t["net_r"]  # net_r is per planned stop loss (fees inside)
        eq += pnl
        taken += 1
        peak = max(peak, eq)
        maxdd = max(maxdd, (peak - eq) / peak)
        if eq <= 0:
            break
    return {"final_equity": round(eq, 4), "return_pct": round(100 * (eq / equity0 - 1), 2),
            "max_dd_pct": round(100 * maxdd, 2), "taken": taken, "skipped_risk": skipped}
