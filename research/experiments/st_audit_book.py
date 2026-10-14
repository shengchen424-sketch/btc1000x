"""ST-AUDIT-001: independent reproduction of the Smart Trader taker-flow book from the rule as mapped
in rg/book/core.py (TOP_N 30 by 30-day rolling median quote volume, min_periods 20; listed >= 180 days;
factor = 7-day sum taker_buy_quote / 7-day sum quote_volume - 0.5, min_periods 5; 5 longs = first 5 of
the top-10 ranks, 5 shorts = first 5 of the bottom-10; weekly rebalance (7-day count) on the completed
daily bar; equal weight, gross 1.0; cost 10 bps of traded notional; trim to entry size when a position
exceeds 2x; funding on held notional). Fractional weights (no lots): the "research form".
Signal on day D's close -> positions applied at D+1 open; return measured open-to-open... the original
engine applies at the next close (daily bars only). We use close(D) -> close(D+1) returns with the
position decided at close(D), which is the same convention as the original daily simulator.
Outputs: per-position records with coin, side, entry/exit, net return; daily leg returns.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from b1k.config import PATHS

TOP_N, MIN_LISTED, FLOW_DAYS, TRIM, COST = 30, 180, 7, 2.0, 0.0010
K = 5
OUT = PATHS.results / "ST-AUDIT-001"


def build_panel() -> pd.DataFrame:
    p = pd.read_parquet(PATHS.data_parquet / "um_1d" / "um_1d.parquet")
    p["date"] = pd.to_datetime(p["open_time"], unit="ms")
    p = p[p["symbol"].str.endswith("USDT")]
    return p


def signals(panel: pd.DataFrame) -> pd.DataFrame:
    """Per (date, symbol): close, universe membership, flow factor, rank. All causal."""
    px = panel.pivot(index="date", columns="symbol", values="close").sort_index()
    qv = panel.pivot(index="date", columns="symbol", values="quote_volume").reindex(px.index)
    tb = panel.pivot(index="date", columns="symbol", values="taker_buy_quote").reindex(px.index)
    listed_days = px.notna().cumsum()
    med30 = qv.rolling(30, min_periods=20).median()
    flow = tb.rolling(FLOW_DAYS, min_periods=5).sum() / qv.rolling(FLOW_DAYS, min_periods=5).sum() - 0.5
    rank_vol = med30.where(listed_days >= MIN_LISTED).rank(axis=1, ascending=False)
    in_univ = rank_vol <= TOP_N
    return px, flow.where(in_univ), in_univ


def simulate(px: pd.DataFrame, flow: pd.DataFrame, funding: pd.DataFrame | None, start: str, end: str,
             offset: int = 0) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = px.index[(px.index >= start) & (px.index <= end)]
    rets = px.pct_change()
    w = pd.Series(0.0, index=px.columns)          # current weights (fraction of equity, signed)
    entry_w = pd.Series(0.0, index=px.columns)
    daily, positions = [], []
    last_reb = None
    open_pos: dict[str, dict] = {}
    for i, d in enumerate(dates):
        r = rets.loc[d].fillna(0.0)
        # mark-to-market: weights drift with returns
        pnl = float((w * r).sum())
        w = w * (1 + r)
        fund = 0.0
        if funding is not None and d in funding.index:
            fr = funding.loc[d].reindex(px.columns).fillna(0.0)
            fund = -float((w * fr).sum())
        cost = 0.0
        # trim
        over = w.abs() > TRIM * entry_w.abs()
        over &= entry_w != 0
        if over.any():
            traded = (w[over].abs() - entry_w[over].abs()).sum()
            cost += COST * traded
            w[over] = entry_w[over]
        due = last_reb is None and (i % 7 == offset) or (last_reb is not None and (d - last_reb).days >= 7)
        if due:
            f = flow.loc[d].dropna()
            if len(f) >= 15:
                ranked = f.sort_values(ascending=False)
                longs = list(ranked.index[:K])
                shorts = [s for s in ranked.index[::-1] if s not in longs][:K]
                target = pd.Series(0.0, index=px.columns)
                target[longs] = 0.1
                target[shorts] = -0.1
                turnover = float((target - w).abs().sum())
                cost += COST * turnover
                # close records
                for s, rec in list(open_pos.items()):
                    if target[s] == 0 or np.sign(target[s]) != np.sign(rec["w0"]):
                        rec["exit_date"] = d; rec["exit_px"] = float(px.loc[d, s])
                        rec["ret"] = (rec["exit_px"] / rec["entry_px"] - 1) * np.sign(rec["w0"])
                        positions.append(rec); del open_pos[s]
                for s in longs + shorts:
                    if s not in open_pos:
                        open_pos[s] = {"symbol": s, "side": "LONG" if target[s] > 0 else "SHORT", "entry_date": d,
                                       "entry_px": float(px.loc[d, s]), "w0": float(target[s]), "flow": float(f.get(s, np.nan))}
                w = target.copy(); entry_w = target.copy(); last_reb = d
        daily.append({"date": d, "gross": pnl, "cost": cost, "funding": fund, "net": pnl - cost + fund,
                      "long_pnl": float((w.clip(lower=0) * 0).sum())})
        daily[-1]["long_ret"] = float((w.clip(lower=0) / (1 + r)).mul(r).sum()) if i else 0.0
        daily[-1]["short_ret"] = float((w.clip(upper=0) / (1 + r)).mul(r).sum()) if i else 0.0
    for s, rec in open_pos.items():
        rec["exit_date"] = dates[-1]; rec["exit_px"] = float(px.loc[dates[-1], s])
        rec["ret"] = (rec["exit_px"] / rec["entry_px"] - 1) * np.sign(rec["w0"]); positions.append(rec)
    return pd.DataFrame(daily).set_index("date"), pd.DataFrame(positions)


def stats(x: pd.Series) -> dict:
    x = x.dropna(); eq = (1 + x).cumprod(); dd = (eq.cummax() - eq) / eq.cummax()
    return {"days": int(len(x)), "ann_pct": round(100 * (eq.iloc[-1] ** (365 / len(x)) - 1), 1),
            "sharpe": round(float(x.mean() / x.std() * np.sqrt(365)), 2), "max_dd_pct": round(100 * float(dd.max()), 1)}


def load_funding_daily(px_index) -> pd.DataFrame | None:
    p = PATHS.data_parquet / "um_1d" / "funding_traded.parquet"
    if not p.exists():
        return None
    f = pd.read_parquet(p)
    f["date"] = pd.to_datetime(f["funding_time"], unit="ms").dt.normalize()
    daily = f.groupby(["date", "symbol"])["rate"].sum().unstack().reindex(px_index).fillna(0.0)
    return daily


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    panel = build_panel()
    px, flow, in_univ = signals(panel)
    start, end = sys.argv[1] if len(sys.argv) > 1 else "2023-01-01", sys.argv[2] if len(sys.argv) > 2 else "2026-09-30"
    funding = None if "--no-funding" in sys.argv else load_funding_daily(px.index)
    print("funding:", "none" if funding is None else f"{funding.shape[1]} symbols")
    allp, alld = [], []
    for off in range(7):
        d, p = simulate(px, flow, funding, start, end, offset=off)
        p["offset"] = off; d["offset"] = off
        allp.append(p); alld.append(d)
        print("offset", off, stats(d["net"]), "positions", len(p), flush=True)
    pos = pd.concat(allp, ignore_index=True); dly = pd.concat(alld)
    pos.to_parquet(OUT / "positions.parquet", index=False); dly.to_parquet(OUT / "daily.parquet")
    pooled = dly.groupby(level=0)["net"].mean()
    print("pooled (mean of 7 offsets)", stats(pooled))
    json.dump({"pooled": stats(pooled), "by_offset": [stats(d["net"]) for d in alld]}, open(OUT / "summary.json", "w"), indent=1)
