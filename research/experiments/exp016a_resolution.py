"""EXP-016a: which reading of the Chainlink TWAP rule matches settled 5m/15m/4h outcomes.
Registration: research/registrations/EXP-016.md. Spot 1 s klines are the stream proxy."""
from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from b1k.config import PATHS
from pmc import spot
from pmc.gamma import event_by_slug

if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "src", "research/experiments"]).returncode:
    sys.exit("refusing to run on uncommitted code")

OUT = PATHS.results / "EXP-016"
CACHE = PATHS.root / "data" / "cache" / "gamma_events"
START = datetime(2026, 10, 20, tzinfo=timezone.utc)
END = datetime(2026, 10, 28, tzinfo=timezone.utc)
SPECS = {"15m": (900, 1), "4h": (14400, 1), "5m": (300, 3)}   # window s, sample every k-th


def slugs():
    for name, (w, k) in SPECS.items():
        t, i = START, 0
        while t + timedelta(seconds=w) <= END:
            if i % k == 0:
                yield name, w, int(t.timestamp()), f"btc-updown-{name}-{int(t.timestamp())}"
            t += timedelta(seconds=w)
            i += 1


def outcome(ev):
    if not ev or not ev.get("markets"):
        return None, None
    m = ev["markets"][0]
    if not m.get("closed"):
        return None, m.get("description")
    prices = [float(x) for x in json.loads(m.get("outcomePrices") or "[]")]
    outs = json.loads(m.get("outcomes") or "[]")
    if len(prices) != 2 or max(prices) < 0.99:
        return None, m.get("description")
    return outs[int(np.argmax(prices))], m.get("description")


def main():
    jobs = list(slugs())
    with ThreadPoolExecutor(4) as ex:
        evs = list(ex.map(lambda j: event_by_slug(j[3], CACHE), jobs))
    days = sorted({(START + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((END - START).days + 1)})
    s1 = pd.concat([spot.day("BTCUSDT", "1s", d) for d in days if spot.day("BTCUSDT", "1s", d) is not None])
    px = pd.Series(s1["close"].values, index=(s1["open_time"] // 1000).values).sort_index()
    px = px[~px.index.duplicated()]
    twap60 = px.rolling(60, min_periods=30).mean()

    rows = []
    for (name, w, t0, slug), ev in zip(jobs, evs):
        out, desc = outcome(ev)
        if out is None:
            continue
        t1 = t0 + w
        try:
            s0, s1_ = px.loc[t0], px.loc[t1 - 1]
            a0, a1 = twap60.loc[t0], twap60.loc[t1 - 1]
        except KeyError:
            continue
        avg = px.loc[t0:t1 - 1].mean()
        up = out == "Up"
        rows.append({"family": name, "slug": slug, "t0": t0, "up": up,
                     "twap_wording": "TWAP" in (desc or ""),
                     "m0": np.log(s1_ / s0), "m1": np.log(a1 / a0), "m2": np.log(avg / a0)})
    df = pd.DataFrame(rows)
    for k in ["0", "1", "2"]:
        df[f"I{k}"] = (df[f"m{k}"] >= 0) == df["up"]
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "016a_markets.csv", index=False)

    lines = ["# EXP-016a results", "", f"Settled markets read: {len(df)} (of {len(jobs)} slugs); "
             f"window {START:%Y-%m-%d} .. {END:%Y-%m-%d}; TWAP wording on {int(df.twap_wording.sum())}.", "",
             "| family | n | I0 spot end-point | I1 TWAP60 end-point | I2 window average |", "|---|---|---|---|---|"]
    for fam, g in df.groupby("family"):
        lines.append(f"| {fam} | {len(g)} | {g.I0.mean():.3f} | {g.I1.mean():.3f} | {g.I2.mean():.3f} |")
    dis = df[((df.m1 >= 0) != (df.m2 >= 0)) & (df.m1.abs() > 2e-4) & (df.m2.abs() > 2e-4)]
    lines += ["", f"Decisive set (I1 and I2 disagree, both margins > 2 bps): n = {len(dis)}; "
              f"I1 matches {dis.I1.mean() if len(dis) else float('nan'):.3f}, I2 matches "
              f"{dis.I2.mean() if len(dis) else float('nan'):.3f}."]
    if len(dis) >= 20 and max(dis.I1.mean(), dis.I2.mean()) >= 0.80:
        verdict = "I1 (end-point)" if dis.I1.mean() > dis.I2.mean() else "I2 (window average)"
    else:
        verdict = "UNRESOLVED"
    lines += ["", f"**Adopted reading: {verdict}**"]
    (OUT / "016a.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
