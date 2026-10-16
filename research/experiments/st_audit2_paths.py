"""ST-AUDIT-002 v2 paths and post-rounding risk check (reproducibility companion, not new evidence).

Re-runs the committed `st_audit2_executable.simulate_lots` logic for the flow book with per-symbol holdings
captured, asserts the daily equity series is identical to the committed function's output, and writes:
  paths/daily_{scen}_{cap}_{off}.parquet      date, equity, net, cost, funding, gross_exp, net_exp, max_sym_exp
  paths/holdings_{scen}_{cap}_{off}.parquet   rebalance date, symbol, qty, notional, exp (= notional/equity)
  risk_after_rounding.csv                     per scenario x capital: per-symbol exposure at rebalance (max, p99),
                                              daily gross / net / single-symbol exposure maxima, margin used at the
                                              live leverage (3x, rg/book/paper.py LEVERAGE) and worst-day headroom.
Usage: python3 st_audit2_paths.py [OPT|CONS ...] [--caps 105,1000] [--out DIR]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st_audit2_executable as X  # noqa: E402
from st_audit_book import build_panel, signals, load_funding_daily, TRIM  # noqa: E402

LEVERAGE = 3  # live: rg/book/paper.py LEVERAGE = 3 (confirmed per order by adapter.ensure_leverage)
FEE, START, END, MIN_EQ = X.FEE, X.START, X.END, X.MIN_TRADABLE_EQUITY


def simulate_paths(px, score, funding, equity0, specs, listing, offset):
    """Copy of X.simulate_lots with holdings capture; equity path asserted equal to the original below."""
    dates = px.index[(px.index >= START) & (px.index <= END)]
    rets = px.pct_change()
    qty = pd.Series(0.0, index=px.columns); entry_notional = pd.Series(0.0, index=px.columns)
    equity, last_reb = equity0, None
    daily, hold = [], []
    for i, d in enumerate(dates):
        p = px.loc[d]; r = rets.loc[d].fillna(0.0); prev_p = p / (1 + r)
        pnl = float((qty * (p - prev_p)).fillna(0.0).sum()); equity += pnl
        fund = 0.0
        if funding is not None and d in funding.index:
            fr = funding.loc[d].reindex(px.columns)
            fund = -float((qty * p * fr.fillna(0.0)).fillna(0.0).sum()); equity += fund
        cost = 0.0
        notional = (qty * p).fillna(0.0)
        over = (notional.abs() > TRIM * entry_notional.abs()) & (entry_notional != 0)
        for s in px.columns[over]:
            new_q = np.sign(qty[s]) * np.floor(abs(entry_notional[s]) / p[s] / specs[s][1]) * specs[s][1]
            cost += FEE * abs(qty[s] - new_q) * p[s]; qty[s] = new_q
        due = (last_reb is None and i % 7 == offset) or (last_reb is not None and (d - last_reb).days >= 7)
        if due and equity >= MIN_EQ:
            f = score.loc[d].dropna()
            if len(f) >= 15:
                tradable = [s for s in f.index if s in listing and listing[s] <= d and s in specs]
                f = f[tradable]
                if len(f) < 15:
                    f = pd.Series(dtype=float)
                ranked = f.sort_values(ascending=False)
                target = equity * 0.1
                longs, shorts, newq = [], [], pd.Series(0.0, index=px.columns)
                for s in ranked.index[:10]:
                    if len(longs) == 5:
                        break
                    q, why = X.placeable(s, p[s], target, specs, listing, d)
                    if q:
                        longs.append(s); newq[s] = q
                for s in ranked.index[::-1][:10]:
                    if len(shorts) == 5:
                        break
                    q, why = X.placeable(s, p[s], target, specs, listing, d)
                    if q:
                        shorts.append(s); newq[s] = -q
                for s in px.columns[(qty != 0) & (newq != 0)]:
                    if np.sign(qty[s]) == np.sign(newq[s]) and abs(qty[s] - newq[s]) * p[s] < 5.5:
                        newq[s] = qty[s]
                traded = float(((newq - qty) * p).abs().fillna(0.0).sum()); cost += FEE * traded
                qty = newq; entry_notional = (qty * p).fillna(0.0)
                last_reb = d
                for s in px.columns[qty != 0]:
                    hold.append({"date": d, "symbol": s, "qty": float(qty[s]), "notional": float(qty[s] * p[s]), "exp": float(qty[s] * p[s] / equity)})
        equity -= cost
        base = equity - pnl - fund + cost
        n = (qty * p).fillna(0.0)
        daily.append({"date": d, "equity": equity, "net": (pnl + fund - cost) / base if base > 0 else 0.0, "cost": cost, "funding": fund,
                      "gross_exp": float(n.abs().sum() / equity), "net_exp": float(n.sum() / equity), "max_sym_exp": float(n.abs().max() / equity)})
    return pd.DataFrame(daily).set_index("date"), pd.DataFrame(hold)


def main():
    args = sys.argv[1:]
    scens = [a for a in args if a in ("OPT", "CONS")] or ["OPT", "CONS"]
    caps = [float(c) for c in args[args.index("--caps") + 1].split(",")] if "--caps" in args else [105.0, 1000.0]
    out = Path(args[args.index("--out") + 1]) if "--out" in args else X.OUT
    (out / "paths").mkdir(parents=True, exist_ok=True)
    panel = build_panel(); px, flow, in_univ = signals(panel); funding = load_funding_daily(px.index); specs = X.load_specs()
    keep = sorted(set(flow.loc[START:END].columns[flow.loc[START:END].notna().any()]) | {"BTCUSDT"})
    px = px[keep]; flow = flow[keep]; funding = funding.reindex(columns=keep) if funding is not None else None
    rows = []
    for scen, buf in [("OPT", 0), ("CONS", 30)]:
        if scen not in scens:
            continue
        listing, _ = X.load_listing(buf)
        for cap in caps:
            agg = []
            for off in range(7):
                dd_ref, _, _, _, _ = X.simulate_lots(px, flow, funding, cap, specs, listing, off)
                dd, hold = simulate_paths(px, flow, funding, cap, specs, listing, off)
                assert np.array_equal(dd_ref["equity"].to_numpy(), dd["equity"].to_numpy()), (scen, cap, off)
                dd.to_parquet(out / "paths" / f"daily_{scen}_{int(cap)}_{off}.parquet"); hold.to_parquet(out / "paths" / f"holdings_{scen}_{int(cap)}_{off}.parquet")
                e = hold["exp"].abs()
                margin_used = dd["gross_exp"] / LEVERAGE  # fraction of equity posted as initial margin at the live leverage
                agg.append({"offset": off, "reb_sym_exp_max": e.max(), "reb_sym_exp_p99": e.quantile(0.99), "reb_sym_exp_median": e.median(),
                            "reb_gross_max": hold.groupby("date")["exp"].apply(lambda s: s.abs().sum()).max(),
                            "daily_sym_exp_max": dd["max_sym_exp"].max(), "daily_gross_max": dd["gross_exp"].max(),
                            "daily_net_max_abs": dd["net_exp"].abs().max(), "margin_used_max": margin_used.max(),
                            "headroom_min": (1 - margin_used).min(), "sizing_violations_gt_15pct": int((e > 0.15).sum()), "n_rebalance_positions": len(hold)})
            a = pd.DataFrame(agg)
            rows.append({"scenario": scen, "capital": cap, **{c: round(float(a[c].max()), 3) for c in a.columns if c != "offset" and c != "headroom_min" and c != "reb_sym_exp_median"},
                         "reb_sym_exp_median": round(float(a["reb_sym_exp_median"].median()), 3), "headroom_min": round(float(a["headroom_min"].min()), 3)})
            print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(out / "risk_after_rounding.csv", index=False)


if __name__ == "__main__":
    main()
