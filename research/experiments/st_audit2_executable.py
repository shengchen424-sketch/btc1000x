"""ST-AUDIT-002: Bitget-executable replay (lots, minimum order, historical listing, 9 bps/side, funding)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from st_audit_book import build_panel, signals, load_funding_daily, stats as bstats, TRIM, K  # noqa: E402
from exp014_relative_value import residual_scores  # noqa: E402
from exp015_blend import z  # noqa: E402

from b1k.config import PATHS

OUT = PATHS.results / "ST-AUDIT-002"
FEE = 0.0006 + 0.0003
START, END = "2023-01-01", "2026-09-30"
CAPITALS = [105.0, 200.0, 300.0, 500.0, 1000.0]


def load_specs():
    c = json.load(open(PATHS.evidence / "exchange" / "bitget_contracts_2026-10-14.json"))["data"]
    return {x["symbol"]: (float(x["minTradeNum"]), float(x["sizeMultiplier"]), float(x.get("minTradeUSDT") or 5)) for x in c}


def load_listing():
    j = json.load(open(PATHS.evidence / "exchange" / "bitget_listing_dates.json"))
    return {k: pd.Timestamp(v["first_daily_bar"]) for k, v in j.items() if not k.startswith("_") and v.get("first_daily_bar")}


def placeable(sym, price, target_usdt, specs, listing, date):
    if sym not in listing or listing[sym] > date:
        return 0.0, "unlisted"
    mn, step, min_usdt = specs.get(sym, (None, None, None))
    if mn is None:
        return 0.0, "nospec"
    qty = np.floor(target_usdt / price / step) * step
    if qty < mn or qty * price < min_usdt:
        return 0.0, "min_order"
    if qty * price < 0.5 * target_usdt:
        return 0.0, "rounding"
    return qty, "ok"


def simulate_lots(px, score, funding, equity0, specs, listing, offset):
    dates = px.index[(px.index >= START) & (px.index <= END)]
    rets = px.pct_change()
    qty = pd.Series(0.0, index=px.columns)        # signed contracts
    entry_notional = pd.Series(0.0, index=px.columns)
    equity = equity0
    last_reb = None
    daily, skips, placed_frac = [], {"unlisted": 0, "min_order": 0, "rounding": 0, "nospec": 0}, []
    top_checks = []
    for i, d in enumerate(dates):
        p = px.loc[d]
        r = rets.loc[d].fillna(0.0)
        prev_p = p / (1 + r)
        pnl = float((qty * (p - prev_p)).fillna(0.0).sum())
        equity += pnl
        fund = 0.0
        if funding is not None and d in funding.index:
            fr = funding.loc[d].reindex(px.columns).fillna(0.0)
            fund = -float((qty * p * fr).fillna(0.0).sum()); equity += fund
        cost = 0.0
        notional = (qty * p).fillna(0.0)
        over = (notional.abs() > TRIM * entry_notional.abs()) & (entry_notional != 0)
        if over.any():
            for s in px.columns[over]:
                new_q = np.sign(qty[s]) * np.floor(abs(entry_notional[s]) / p[s] / specs[s][1]) * specs[s][1]
                cost += FEE * abs(qty[s] - new_q) * p[s]; qty[s] = new_q
        due = (last_reb is None and i % 7 == offset) or (last_reb is not None and (d - last_reb).days >= 7)
        if due:
            f = score.loc[d].dropna()
            if len(f) >= 15:
                ranked = f.sort_values(ascending=False)
                target_usdt = equity * 0.1
                longs, shorts, newq = [], [], pd.Series(0.0, index=px.columns)
                for s in ranked.index[:10]:
                    q, why = placeable(s, p[s], target_usdt, specs, listing, d)
                    if q > 0 and len(longs) < K:
                        longs.append(s); newq[s] = q
                    elif len(longs) < K:
                        skips[why] += 1
                for s in ranked.index[::-1][:10]:
                    if s in longs:
                        continue
                    q, why = placeable(s, p[s], target_usdt, specs, listing, d)
                    if q > 0 and len(shorts) < K:
                        shorts.append(s); newq[s] = -q
                    elif len(shorts) < K:
                        skips[why] += 1
                traded = float(((newq - qty) * p).abs().fillna(0.0).sum())
                cost += FEE * traded
                qty = newq; entry_notional = (qty * p).fillna(0.0)
                placed_frac.append(float((qty * p).abs().sum()) / (equity * 1.0) if equity > 0 else 0.0)
                last_reb = d
        equity -= cost
        daily.append({"date": d, "equity": equity, "net": (pnl + fund - cost) / (equity - pnl - fund + cost) if equity - pnl - fund + cost > 0 else 0.0,
                      "cost": cost, "funding": fund})
        if equity <= 0:
            break
    dd = pd.DataFrame(daily).set_index("date")
    return dd, skips, float(np.mean(placed_frac)) if placed_frac else 0.0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    panel = build_panel()
    px, flow, in_univ = signals(panel)
    funding = load_funding_daily(px.index)
    specs, listing = load_specs(), load_listing()
    rm14 = residual_scores(px, in_univ, 14)
    books = {"A_flow": flow, "RM14": rm14, "BLEND25": (z(flow) + 0.5 * z(rm14)).where(in_univ & flow.notna() & rm14.notna())}
    research = {"A_flow": pd.read_parquet(PATHS.results / "EXP-013" / "daily_A.parquet")["A"],
                "RM14": pd.read_parquet(PATHS.results / "EXP-014" / "daily_RM14.parquet")["RM14"],
                "BLEND25": pd.read_parquet(PATHS.results / "EXP-015" / "daily_BLEND25.parquet")["BLEND25"]}
    rows = []
    for name, score in books.items():
        rs = bstats(research[name][START:END])
        for cap in CAPITALS:
            runs, sk, pf = [], {"unlisted": 0, "min_order": 0, "rounding": 0, "nospec": 0}, []
            for off in range(7):
                dd, skips, frac = simulate_lots(px, score, funding, cap, specs, listing, off)
                runs.append(dd["net"]); pf.append(frac)
                for k in sk: sk[k] += skips[k]
            pooled = pd.concat(runs, axis=1).mean(axis=1)
            s = bstats(pooled)
            cost_yr = float(np.mean([pd.concat(runs, axis=1).shape[0]]))  # placeholder count
            row = {"book": name, "capital": cap, **{f"exec_{k}": v for k, v in s.items()}, "research_ann_pct": rs["ann_pct"],
                   "research_sharpe": rs["sharpe"], "ratio_exec_over_research": round(s["ann_pct"] / rs["ann_pct"], 2) if rs["ann_pct"] else None,
                   "placed_fraction": round(float(np.mean(pf)), 3), **{f"skips_{k}": v // 7 for k, v in sk.items()}}
            rows.append(row)
            print({k: row[k] for k in ["book", "capital", "exec_ann_pct", "exec_sharpe", "exec_max_dd_pct", "research_ann_pct", "ratio_exec_over_research", "placed_fraction", "skips_unlisted", "skips_min_order", "skips_rounding"]}, flush=True)
    pd.DataFrame(rows).to_csv(OUT / "executable_table.csv", index=False)
    # top-1% research positions: listed at entry? placeable at 105?
    pos = pd.read_parquet(PATHS.results / "ST-AUDIT-001" / "positions.parquet")
    top = pos.sort_values("ret", ascending=False).head(85).copy()
    top["listed_at_entry"] = [s in listing and listing[s] <= pd.Timestamp(d) for s, d in zip(top.symbol, top.entry_date)]
    top["placeable_105"] = [placeable(s, p0, 10.5, specs, listing, pd.Timestamp(d))[1] == "ok" for s, p0, d in zip(top.symbol, top.entry_px, top.entry_date)]
    top[["symbol", "side", "entry_date", "ret", "listed_at_entry", "placeable_105"]].to_csv(OUT / "top85_positions_executability.csv", index=False)
    print("top-1% research positions: listed at entry", round(top.listed_at_entry.mean(), 3), "| placeable at 105 USDT", round(top.placeable_105.mean(), 3),
          "| pnl share of those listed+placeable", round(top.loc[top.listed_at_entry & top.placeable_105, "ret"].sum() / top.ret.sum(), 3))


if __name__ == "__main__":
    main()
