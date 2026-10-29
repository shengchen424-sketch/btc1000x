"""Census of live crypto markets: family, resolution text template, fee schedule, tick, liquidity.

python -m pmc.census --tag bitcoin --out research/results/PM-CENSUS
Writes census.csv (one row per market) and templates.md (distinct normalised resolution texts per
family), so a rule change on Polymarket shows up as a new template."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from pmc.families import family
from pmc.gamma import active_events


def _template(text: str) -> str:
    t = re.sub(r"\d[\d,\.]*", "#", text or "")
    t = re.sub(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b", "MON", t)
    return re.sub(r"\s+", " ", t).strip()


def run(tag: str, out: Path) -> pd.DataFrame:
    events = active_events(tag)
    rows, templates = [], defaultdict(lambda: defaultdict(int))
    for ev in events:
        fam = family(ev.get("slug", ""))
        for m in ev.get("markets", []):
            fs = m.get("feeSchedule") or {}
            desc = m.get("description") or ev.get("description") or ""
            tpl = _template(desc)
            templates[fam or "other"][tpl] += 1
            rows.append({
                "event_slug": ev.get("slug"), "family": fam, "market_slug": m.get("slug"),
                "item": m.get("groupItemTitle"), "end": m.get("endDate"),
                "start": m.get("eventStartTime") or m.get("startDate"),
                "resolution_source": m.get("resolutionSource"),
                "tpl_sha": hashlib.sha256(tpl.encode()).hexdigest()[:12],
                "fees_enabled": m.get("feesEnabled"), "fee_type": m.get("feeType"),
                "fee_rate": fs.get("rate"), "fee_exponent": fs.get("exponent"),
                "fee_taker_only": fs.get("takerOnly"), "rebate_rate": fs.get("rebateRate"),
                "twap_lookback_s": (m.get("cryptoMarketConfig") or {}).get("twapLookbackSeconds"),
                "tick": m.get("orderPriceMinTickSize"), "min_size": m.get("orderMinSize"),
                "neg_risk": m.get("negRisk"), "liquidity": m.get("liquidityNum"),
                "volume24h": m.get("volume24hr"), "best_bid": m.get("bestBid"),
                "best_ask": m.get("bestAsk"), "spread": m.get("spread"),
                "fallback": m.get("fallbackResolutionType"),
            })
    df = pd.DataFrame(rows)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "census.csv", index=False)
    with open(out / "templates.md", "w") as f:
        f.write(f"# Resolution-text templates, tag={tag}, {datetime.now(timezone.utc):%Y-%m-%dT%H:%MZ}\n\n")
        for fam in sorted(templates):
            f.write(f"## {fam}\n\n")
            for tpl, n in sorted(templates[fam].items(), key=lambda x: -x[1]):
                f.write(f"- n={n} `{hashlib.sha256(tpl.encode()).hexdigest()[:12]}`: {tpl}\n")
            f.write("\n")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="bitcoin")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    df = run(a.tag, a.out)
    print(df.groupby("family", dropna=False).agg(
        markets=("market_slug", "size"), templates=("tpl_sha", "nunique"),
        fee_rate=("fee_rate", lambda s: sorted(set(s.dropna()))),
        fee_exp=("fee_exponent", lambda s: sorted(set(s.dropna()))),
        tick=("tick", lambda s: sorted(set(s.dropna()))),
        med_liq=("liquidity", "median"), med_spread=("spread", "median")).to_string())
