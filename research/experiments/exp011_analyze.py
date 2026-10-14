"""EXP-011 analysis: Part A market calibration; Part B ensemble vs market (bias fit on first 45 days,
evaluated on last 45 days), simulated edge rule. Reads research/results/EXP-011/data/."""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp001_baseline import git_head  # noqa: E402

from b1k.config import PATHS

D = PATHS.results / "EXP-011" / "data"
OUT = PATHS.results / "EXP-011"


def load_events():
    """Re-parse bucket bounds from the question text (the fetch script's first version mis-parsed
    the open-ended buckets); drop events whose buckets do not form a complete partition."""
    from exp011_fetch import parse_bucket
    out = []
    for l in open(D / "bucket_prices.jsonl"):
        e = json.loads(l)
        ok = True
        for b in e["buckets"]:
            pb = parse_bucket(b["q"] or "")
            if pb is None:
                ok = False
                break
            b["lo"], b["hi"], b["unit"] = pb
        if ok and len(e["buckets"]) >= 5:
            out.append(e)
    return out


def load_ens(city):
    p = D / f"ens_{city.replace(' ', '_')}.json"
    if not p.exists():
        return None
    j = json.load(open(p))
    dd = j["daily"]
    members = [k for k in dd if k.startswith("temperature_2m_max")]
    out = {}
    for i, t in enumerate(dd["time"]):
        vals = [dd[k][i] for k in members if dd[k][i] is not None]
        if vals:
            out[t] = np.array(vals, float)
    return out


def to_unit(vals_f: np.ndarray, unit: str) -> np.ndarray:
    return vals_f if unit == "F" else (vals_f - 32) * 5 / 9


def bucket_prob(members: np.ndarray, lo: int, hi: int, sigma: float) -> float:
    """Each member is a Gaussian kernel; probability that the rounded temperature lands in [lo, hi]."""
    a, b = (lo - 0.5 if lo > -999 else -1e9), (hi + 0.5 if hi < 999 else 1e9)
    return float(np.mean(stats.norm.cdf((b - members) / sigma) - stats.norm.cdf((a - members) / sigma)))


def part_a(events):
    rows = []
    for e in events:
        bs = [b for b in e["buckets"] if b["resolved_yes"] is not None]
        if len(bs) < 5:
            continue
        for key in ("p06", "p12prev"):
            ps = [b[key] for b in bs]
            if any(p is None for p in ps):
                continue
            for b in bs:
                rows.append({"t": key, "p": b[key], "y": b["resolved_yes"], "city": e["city"], "day": e["day"], "sum": sum(ps)})
    out = {}
    for key in ("p06", "p12prev"):
        r = [x for x in rows if x["t"] == key]
        if not r:
            continue
        p = np.array([x["p"] for x in r]); y = np.array([x["y"] for x in r])
        bins = [0, .02, .05, .1, .2, .3, .5, .7, 1.01]
        rel = []
        for lo, hi in zip(bins[:-1], bins[1:]):
            m = (p >= lo) & (p < hi)
            if m.sum():
                rel.append({"bin": f"[{lo},{hi})", "n": int(m.sum()), "mean_price": float(p[m].mean()), "hit_rate": float(y[m].mean())})
        out[key] = {"n_buckets": int(len(r)), "n_events": len({(x['city'], x['day']) for x in r}),
                    "brier": float(np.mean((p - y) ** 2)), "brier_uniform_1of11": float(np.mean((1 / 11 - y) ** 2)),
                    "mean_sum_of_prices": float(np.mean([x["sum"] for x in r])), "reliability": rel}
    return out


def part_b(events, edge=0.10, max_price=0.60):
    by_city = defaultdict(list)
    for e in events:
        by_city[e["city"]].append(e)
    days_all = sorted({e["day"] for e in events})
    recs = []
    for city, evs in by_city.items():
        ens = load_ens(city)
        if ens is None:
            continue
        evs = sorted(evs, key=lambda e: e["day"])
        have = [e for e in evs if e["day"] in ens and all(b["p06"] is not None for b in e["buckets"]) and len(e["buckets"]) >= 5]
        if len(have) < 20:
            continue
        split = len(have) // 2
        fit, test = have[:split], have[split:]
        # bias: realised bucket midpoint (the resolved bucket) minus ensemble mean, in the market's unit
        errs = []
        for e in fit:
            unit = e["buckets"][0]["unit"]
            mem = to_unit(ens[e["day"]], unit)
            won = [b for b in e["buckets"] if b["resolved_yes"] == 1.0]
            if won:
                lo, hi = won[0]["lo"], won[0]["hi"]
                mid = (lo + hi) / 2 if lo > -999 and hi < 999 else (hi if lo == -999 else lo)
                errs.append(mid - mem.mean())
        bias = float(np.mean(errs)) if errs else 0.0
        for e in test:
            unit = e["buckets"][0]["unit"]
            mem = to_unit(ens[e["day"]], unit) + bias
            sigma = max(float(mem.std()), 1.0 if unit == "F" else 0.6)
            for b in e["buckets"]:
                pm = bucket_prob(mem, b["lo"], b["hi"], sigma)
                recs.append({"city": city, "day": e["day"], "p_model": pm, "p_mkt": b["p06"], "y": b["resolved_yes"],
                             "fee": b.get("fees"), "bias": bias, "sigma": sigma})
    if not recs:
        return {"n": 0}
    pm = np.array([r["p_model"] for r in recs]); pk = np.array([r["p_mkt"] for r in recs]); y = np.array([r["y"] for r in recs])
    d = (pk - y) ** 2 - (pm - y) ** 2  # positive = model better
    rng = np.random.default_rng(3)
    # paired bootstrap by event
    keys = sorted({(r["city"], r["day"]) for r in recs})
    idx = defaultdict(list)
    for i, r in enumerate(recs):
        idx[(r["city"], r["day"])].append(i)
    boots = []
    for _ in range(4000):
        samp = rng.integers(0, len(keys), len(keys))
        ii = np.concatenate([idx[keys[s]] for s in samp])
        boots.append(d[ii].mean())
    lo, hi = np.quantile(boots, [0.025, 0.975])
    # edge rule
    bets = []
    for r in recs:
        if r["p_model"] - r["p_mkt"] >= edge and r["p_mkt"] <= max_price:
            price = r["p_mkt"] + 0.01
            ret = (1.0 - price) if r["y"] == 1.0 else -price
            bets.append(ret / price)  # return per unit staked
    bets = np.array(bets)
    tb = stats.ttest_1samp(bets, 0.0) if len(bets) > 1 else (float("nan"), float("nan"))
    per_city = {}
    for c in sorted({r["city"] for r in recs}):
        m = np.array([r["city"] == c for r in recs])
        per_city[c] = {"n_buckets": int(m.sum()), "brier_model": float(((pm - y) ** 2)[m].mean()), "brier_mkt": float(((pk - y) ** 2)[m].mean()),
                       "bias_used": recs[int(np.where(m)[0][0])]["bias"]}
    return {"n_buckets": int(len(recs)), "n_events": len(keys), "brier_model": float(((pm - y) ** 2).mean()),
            "brier_market": float(((pk - y) ** 2).mean()), "diff_mean": float(d.mean()), "diff_ci95": [float(lo), float(hi)],
            "edge_rule": {"edge": edge, "max_price": max_price, "n_bets": int(len(bets)),
                          "mean_return_per_unit": float(bets.mean()) if len(bets) else None,
                          "win_rate": float((bets > 0).mean()) if len(bets) else None,
                          "p_one_sided": float(tb[1] / 2 if len(bets) > 1 and tb[0] > 0 else (1 - tb[1] / 2 if len(bets) > 1 else float("nan")))},
            "per_city": per_city}


def main():
    events = load_events()
    a = part_a(events)
    b = part_b(events)
    lead = bool(b.get("n_buckets", 0) and b["diff_ci95"][0] > 0 and b["edge_rule"]["n_bets"] >= 40
                and b["edge_rule"]["mean_return_per_unit"] > 0 and b["edge_rule"]["p_one_sided"] < 0.05)
    res = {"experiment": "EXP-011", "git_head": git_head(), "events_with_prices": len(events), "part_a": a, "part_b": b,
           "gate": "LEAD" if lead else "NO_EVIDENCE"}
    (OUT / "verdict.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: res[k] for k in ["events_with_prices", "gate"]}))
    print(json.dumps(a, indent=1)[:1500])
    print(json.dumps({k: v for k, v in b.items() if k != "per_city"}, indent=1))
    print(json.dumps(b.get("per_city", {}), indent=1)[:2500])


if __name__ == "__main__":
    main()
