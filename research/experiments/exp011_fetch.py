"""EXP-011 data fetch: bucket prices at decision times for closed temperature events + GFS ensemble
daily maxima at resolution stations (last 92 days). Writes research/results/EXP-011/data/*.json."""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

from b1k.config import PATHS

OUT = PATHS.results / "EXP-011" / "data"
OUT.mkdir(parents=True, exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = "btc1000x-research/0.1 (github shengchen424-sketch/btc1000x)"

# resolution stations (from market descriptions) -> coordinates
STATIONS = {
    "NYC": (40.7772, -73.8726, "KLGA LaGuardia"), "Chicago": (41.9742, -87.9073, "KORD O'Hare"),
    "Miami": (25.7959, -80.2870, "KMIA"), "Los Angeles": (33.9416, -118.4085, "KLAX"),
    "Denver": (39.7017, -104.7517, "KBKF Buckley"), "Dallas": (32.8471, -96.8518, "KDAL Love Field"),
    "Atlanta": (33.6407, -84.4277, "KATL"), "Houston": (29.9902, -95.3368, "KIAH"),
    "Seattle": (47.4502, -122.3088, "KSEA"), "Toronto": (43.6777, -79.6248, "CYYZ Pearson"),
    "Sao Paulo": (-23.4356, -46.4731, "SBGR Guarulhos"), "London": (51.5048, 0.0495, "EGLC City"),
    "Paris": (49.0097, 2.5479, "LFPG CDG"),
}
TAIL_RE = re.compile(r"be (-?\d+)°([CF]) or (below|higher|lower|above)")
RANGE_RE = re.compile(r"be (?:between )?(-?\d+)(?:-(-?\d+))?°([CF])")


def parse_bucket(q: str):
    """Open-ended buckets first ('61°F or below', '80°F or higher'), then ranges / single values."""
    m = TAIL_RE.search(q)
    if m:
        v, unit, side = int(m.group(1)), m.group(2), m.group(3)
        return (-999, v, unit) if side in ("below", "lower") else (v, 999, unit)
    m = RANGE_RE.search(q)
    if not m:
        return None
    lo = int(m.group(1)); hi = int(m.group(2)) if m.group(2) else lo
    return lo, hi, m.group(3)


def price_at(hist: list[dict], t_ms: int) -> float | None:
    best = None
    for h in hist:
        if h["t"] * 1000 <= t_ms:
            best = h["p"]
        else:
            break
    return best


def fetch_prices(events_path: Path, cities: set[str], since: str) -> None:
    rows = json.load(open(events_path))
    out_p = OUT / "bucket_prices.jsonl"
    done = set()
    if out_p.exists():
        done = {json.loads(l)["event_id"] for l in open(out_p)}
    n = 0
    with open(out_p, "a") as f:
        for e in rows:
            city = e["title"].split(" in ")[1].split(" on ")[0]
            if city not in cities or e["id"] in done or (e["endDate"] or "") < since:
                continue
            end = datetime.fromisoformat(e["endDate"].replace("Z", "+00:00"))
            # observation day D = the date in the title; decision 06:00 UTC D and 12:00 UTC D-1
            d_day = end.date()
            t06 = int(datetime(d_day.year, d_day.month, d_day.day, 6, tzinfo=timezone.utc).timestamp() * 1000)
            t12p = int((datetime(d_day.year, d_day.month, d_day.day, 12, tzinfo=timezone.utc) - timedelta(days=1)).timestamp() * 1000)
            buckets = []
            for m in e["markets"]:
                b = parse_bucket(m["q"] or "")
                tok = m["tokens"][0] if m["tokens"] else None
                if b is None or tok is None:
                    continue
                try:
                    r = S.get("https://clob.polymarket.com/prices-history",
                              params={"market": tok, "interval": "max", "fidelity": 60}, timeout=30)
                    hist = r.json().get("history", []) if r.status_code == 200 else []
                except Exception:
                    hist = []
                final = json.loads(m["final"]) if isinstance(m["final"], str) else (m["final"] or [None, None])
                buckets.append({"q": m["q"], "lo": b[0], "hi": b[1], "unit": b[2], "p06": price_at(hist, t06),
                                "p12prev": price_at(hist, t12p), "resolved_yes": float(final[0]) if final and final[0] is not None else None,
                                "n_hist": len(hist), "fees": m.get("fees"), "spread": m.get("spread")})
                time.sleep(0.15)
            f.write(json.dumps({"event_id": e["id"], "city": city, "day": d_day.isoformat(), "buckets": buckets}) + "\n")
            f.flush()
            n += 1
            if n % 20 == 0:
                print("events fetched", n, flush=True)
    print("done, new events:", n)


def fetch_ensembles() -> None:
    for city, (lat, lon, name) in STATIONS.items():
        p = OUT / f"ens_{city.replace(' ', '_')}.json"
        if p.exists():
            continue
        r = S.get("https://ensemble-api.open-meteo.com/v1/ensemble",
                  params={"latitude": lat, "longitude": lon, "daily": "temperature_2m_max", "models": "gfs025",
                          "past_days": 92, "forecast_days": 1, "temperature_unit": "fahrenheit"}, timeout=60)
        j = r.json()
        j["_station"] = name
        p.write_text(json.dumps(j))
        print(city, r.status_code, len(j.get("daily", {}).get("time", [])), flush=True)
        time.sleep(1.0)


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "ens":
        fetch_ensembles()
    else:
        fetch_prices(Path(sys.argv[2]), set(STATIONS), since=sys.argv[3] if len(sys.argv) > 3 else "2025-01-01")
