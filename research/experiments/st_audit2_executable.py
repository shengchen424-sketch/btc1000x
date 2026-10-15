"""ST-AUDIT-002: Bitget-executable replay under today's contract rules, with historical eligibility scenarios.

Eligibility evidence classes (evidence/exchange/bitget_listing_dates.json):
  EARLIEST-QUOTE : first daily candle Bitget's history-candles serves (paged to exhaustion; no retention
                   cluster was found across symbols, but this is "earliest observable quote", not a
                   confirmed listing announcement).
  ABSENT         : no Bitget candle data under the Binance symbol or its 1000-prefix alias: delisted,
                   renamed, or never listed. Treated as unlisted in every scenario (reported as a gap).
Scenarios: OPT = eligible from the earliest quote; CONS = eligible 30 days after the earliest quote.
Specs (step, minimum) are TODAY's; funding is Binance realised funding (Bitget history covers ~3 months);
missing funding = 0 and counted. Rounding: qty = floor(target / price / step) * step; skip if
qty*price < 5 USDT or < 50 % of target; a skipped slot stays in cash (no re-allocation), as live.
"""
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
MIN_TRADABLE_EQUITY = 50.0   # below this a 10 % slot is under the 5 USDT minimum: the book cannot be placed


def load_specs():
    c = json.load(open(PATHS.evidence / "exchange" / "bitget_contracts_2026-10-14.json"))["data"]
    return {x["symbol"]: (float(x["minTradeNum"]), float(x["sizeMultiplier"]), float(x.get("minTradeUSDT") or 5)) for x in c}


def load_listing(buffer_days: int):
    j = json.load(open(PATHS.evidence / "exchange" / "bitget_listing_dates.json"))
    out, cls = {}, {}
    for k, v in j.items():
        if k.startswith("_"):
            continue
        if v.get("first_daily_bar"):
            out[k] = pd.Timestamp(v["first_daily_bar"]) + pd.Timedelta(days=buffer_days); cls[k] = "EARLIEST-QUOTE"
        else:
            cls[k] = "ABSENT"
    return out, cls


def placeable(sym, price, target_usdt, specs, listing, date):
    if sym not in listing or listing[sym] > date:
        return 0.0, "unlisted"
    mn, step, min_usdt = specs.get(sym, (None, None, None))
    if mn is None:
        return 0.0, "unlisted"  # no current spec = not on Bitget today
    qty = np.floor(target_usdt / price / step) * step
    if qty < mn or qty * price < min_usdt:
        return 0.0, "min_order"
    if qty * price < 0.5 * target_usdt:
        return 0.0, "rounding"
    return qty, "ok"


def simulate_lots(px, score, funding, equity0, specs, listing, offset):
    dates = px.index[(px.index >= START) & (px.index <= END)]
    rets = px.pct_change()
    qty = pd.Series(0.0, index=px.columns)
    entry_notional = pd.Series(0.0, index=px.columns)
    equity, last_reb = equity0, None
    daily, rebs = [], []
    skips = {"unlisted": 0, "min_order": 0, "rounding": 0}
    missing_funding_days = 0
    dead_date = None
    for i, d in enumerate(dates):
        p = px.loc[d]; r = rets.loc[d].fillna(0.0); prev_p = p / (1 + r)
        pnl = float((qty * (p - prev_p)).fillna(0.0).sum()); equity += pnl
        fund = 0.0
        if funding is not None and d in funding.index:
            fr = funding.loc[d].reindex(px.columns)
            held = qty != 0
            missing_funding_days += int((held & fr.isna()).sum())
            fund = -float((qty * p * fr.fillna(0.0)).fillna(0.0).sum()); equity += fund
        cost = 0.0
        notional = (qty * p).fillna(0.0)
        over = (notional.abs() > TRIM * entry_notional.abs()) & (entry_notional != 0)
        for s in px.columns[over]:
            new_q = np.sign(qty[s]) * np.floor(abs(entry_notional[s]) / p[s] / specs[s][1]) * specs[s][1]
            cost += FEE * abs(qty[s] - new_q) * p[s]; qty[s] = new_q
        due = (last_reb is None and i % 7 == offset) or (last_reb is not None and (d - last_reb).days >= 7)
        if due and equity >= MIN_TRADABLE_EQUITY:
            f = score.loc[d].dropna()
            if len(f) >= 15:
                ranked = f.sort_values(ascending=False)
                target = equity * 0.1
                longs, shorts, newq = [], [], pd.Series(0.0, index=px.columns)
                for s in ranked.index[:10]:
                    if len(longs) >= K:
                        break
                    q, why = placeable(s, p[s], target, specs, listing, d)
                    if q > 0:
                        longs.append(s); newq[s] = q
                    else:
                        skips[why] += 1
                for s in ranked.index[::-1][:10]:
                    if len(shorts) >= K:
                        break
                    if s in longs:
                        continue
                    q, why = placeable(s, p[s], target, specs, listing, d)
                    if q > 0:
                        shorts.append(s); newq[s] = -q
                    else:
                        skips[why] += 1
                traded = float(((newq - qty) * p).abs().fillna(0.0).sum()); cost += FEE * traded
                qty = newq; entry_notional = (qty * p).fillna(0.0)
                L = float(entry_notional[entry_notional > 0].sum()); S_ = float(-entry_notional[entry_notional < 0].sum())
                rebs.append({"date": d, "long_exp": L / equity, "short_exp": S_ / equity, "net_exp": (L - S_) / equity,
                             "cash_frac": 1 - (L + S_) / equity, "n_long": len(longs), "n_short": len(shorts)})
                last_reb = d
        elif due and dead_date is None:
            dead_date = d
        equity -= cost
        base = equity - pnl - fund + cost
        daily.append({"date": d, "equity": equity, "net": (pnl + fund - cost) / base if base > 0 else 0.0, "cost": cost, "funding": fund})
    dd = pd.DataFrame(daily).set_index("date")
    return dd, pd.DataFrame(rebs), skips, missing_funding_days, dead_date


def run(books, research, px, funding, specs, scen, listing, cls):
    rows = []
    for name, score in books.items():
        rs = bstats(research[name][START:END])
        for cap in CAPITALS:
            per_off = []
            for off in range(7):
                dd, rebs, skips, miss, dead = simulate_lots(px, score, funding, cap, specs, listing, off)
                s = bstats(dd["net"])
                per_off.append({"offset": off, **s, "final_equity": round(float(dd["equity"].iloc[-1]), 2),
                                "min_equity": round(float(dd["equity"].min()), 2), "dead_date": str(dead.date()) if dead is not None else None,
                                "cost_pct_yr": round(100 * dd["cost"].sum() / cap / (len(dd) / 365), 1),
                                "funding_pct_yr": round(100 * dd["funding"].sum() / cap / (len(dd) / 365), 1),
                                "missing_funding_days": miss, **{f"skips_{k}": v for k, v in skips.items()},
                                "avg_long_exp": round(float(rebs["long_exp"].mean()), 3) if len(rebs) else None,
                                "avg_short_exp": round(float(rebs["short_exp"].mean()), 3) if len(rebs) else None,
                                "avg_net_exp": round(float(rebs["net_exp"].mean()), 3) if len(rebs) else None,
                                "max_abs_net_exp": round(float(rebs["net_exp"].abs().max()), 3) if len(rebs) else None,
                                "avg_cash_frac": round(float(rebs["cash_frac"].mean()), 3) if len(rebs) else None,
                                "avg_positions": round(float((rebs["n_long"] + rebs["n_short"]).mean()), 1) if len(rebs) else None})
            df = pd.DataFrame(per_off)
            worst = df.loc[df["ann_pct"].idxmin()]
            row = {"scenario": scen, "book": name, "capital": cap, "research_ann_pct": rs["ann_pct"], "research_sharpe": rs["sharpe"],
                   "exec_ann_median": float(df["ann_pct"].median()), "exec_ann_worst": float(worst["ann_pct"]), "exec_sharpe_median": float(df["sharpe"].median()),
                   "exec_sharpe_worst": float(df["sharpe"].min()), "exec_maxdd_worst": float(df["max_dd_pct"].max()),
                   "min_equity_worst": float(df["min_equity"].min()), "dead_offsets": int(df["dead_date"].notna().sum()),
                   "cost_pct_yr": float(df["cost_pct_yr"].median()), "funding_pct_yr": float(df["funding_pct_yr"].median()),
                   "avg_positions": float(df["avg_positions"].median()), "avg_long_exp": float(df["avg_long_exp"].median()),
                   "avg_short_exp": float(df["avg_short_exp"].median()), "avg_net_exp": float(df["avg_net_exp"].median()),
                   "max_abs_net_exp": float(df["max_abs_net_exp"].max()), "avg_cash_frac": float(df["avg_cash_frac"].median()),
                   "skips_unlisted": int(df["skips_unlisted"].median()), "skips_min_order": int(df["skips_min_order"].median()),
                   "skips_rounding": int(df["skips_rounding"].median()), "missing_funding_days": int(df["missing_funding_days"].median())}
            rows.append(row)
            df.to_csv(OUT / f"offsets_{scen}_{name}_{int(cap)}.csv", index=False)
            print(scen, name, cap, "exec ann med/worst", row["exec_ann_median"], row["exec_ann_worst"], "| research", rs["ann_pct"],
                  "| pos", row["avg_positions"], "net_exp", row["avg_net_exp"], "cash", row["avg_cash_frac"], "| skips U/M/R",
                  row["skips_unlisted"], row["skips_min_order"], row["skips_rounding"], "| dead", row["dead_offsets"], flush=True)
    return rows


def top85_table(specs, listing_opt, cls):
    pos = pd.read_parquet(PATHS.results / "ST-AUDIT-001" / "positions.parquet")
    top = pos.sort_values("ret", ascending=False).head(85).copy()
    rows = []
    for _, t in top.iterrows():
        d = pd.Timestamp(t.entry_date)
        listed = t.symbol in listing_opt and listing_opt[t.symbol] <= d
        q, why = placeable(t.symbol, t.entry_px, 10.5, specs, listing_opt, d)
        notional = q * t.entry_px
        rows.append({"symbol": t.symbol, "side": t.side, "entry_date": str(d.date()), "exit_date": str(pd.Timestamp(t.exit_date).date()),
                     "research_ret_pct": round(100 * t.ret, 1), "evidence": cls.get(t.symbol, "ABSENT"),
                     "bitget_first_quote": str(listing_opt[t.symbol].date()) if t.symbol in listing_opt else None,
                     "tradable_at_entry": bool(listed), "qty_at_105usdt": q, "notional_at_105": round(notional, 2),
                     "reason": why, "retained_profit_frac": round(notional / 10.5, 3) if q > 0 else 0.0})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "top85_positions_executability.csv", index=False)
    w = df["research_ret_pct"]
    print("top-85: tradable at entry", round(df.tradable_at_entry.mean(), 3), "| placeable at 105", round((df.reason == "ok").mean(), 3),
          "| profit retained (notional-weighted)", round(float((w * df.retained_profit_frac).sum() / w.sum()), 3))
    return df


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    panel = build_panel()
    px, flow, in_univ = signals(panel)
    funding = load_funding_daily(px.index)
    specs = load_specs()
    rm14 = residual_scores(px, in_univ, 14)
    books = {"A_flow": flow, "RM14": rm14, "BLEND25": (z(flow) + 0.5 * z(rm14)).where(in_univ & flow.notna() & rm14.notna())}
    research = {"A_flow": pd.read_parquet(PATHS.results / "EXP-013" / "daily_A.parquet")["A"],
                "RM14": pd.read_parquet(PATHS.results / "EXP-014" / "daily_RM14.parquet")["RM14"],
                "BLEND25": pd.read_parquet(PATHS.results / "EXP-015" / "daily_BLEND25.parquet")["BLEND25"]}
    rows = []
    for scen, buf in [("OPT", 0), ("CONS", 30)]:
        listing, cls = load_listing(buf)
        rows += run(books, research, px, funding, specs, scen, listing, cls)
    pd.DataFrame(rows).to_csv(OUT / "executable_table.csv", index=False)
    listing, cls = load_listing(0)
    top85_table(specs, listing, cls)
    pos = pd.read_parquet(PATHS.results / "ST-AUDIT-001" / "positions.parquet"); pos["pnl"] = pos.ret * 0.1
    absent = [s for s, c in cls.items() if c == "ABSENT"]
    print("ABSENT symbols:", len(absent), "| pnl share:", round(pos[pos.symbol.isin(absent)].pnl.sum() / pos.pnl.sum(), 3))


if __name__ == "__main__":
    main()
