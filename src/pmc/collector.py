"""Forward order-book collector for Polymarket crypto window markets (read-only, no key, no orders).

Why: Polymarket keeps no public book history, so every later market experiment is built on what
this records. One CLOB book per market (the first outcome token; the second is its mirror,
checked 2026-10-29: Down bids = 1 - Up asks), top LEVELS levels each side.

Cadence: markets whose window has started and ends within 1 h: every FAST_S; other open markets:
every SLOW_S. Catalogue refresh every CATALOG_S (tag listing + generated 5m/15m/4h slugs).
Output: <out>/YYYY-MM-DD/HH.jsonl.gz, one line per book; catalog.jsonl with each market's rule,
fee schedule and token ids the first time it is seen.

Guards: stop when the output directory exceeds --max-gb, or when free disk falls below
--min-free-gb (host GUARD_POLICY: collectors stop below 55 GiB). Stopping writes STOPPED.json.

python -m pmc.collector --out /root/polymarket-btc-hunter/data/pm_books
"""
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from pmc.families import family
from pmc.gamma import CLOB, active_events, event_by_slug

LEVELS = 8
FAST_S, SLOW_S, CATALOG_S = 10, 120, 300
WINDOWS = {"5m": 300, "15m": 900, "4h": 14400}
_stop = False


def _now() -> float:
    return time.time()


def _iso(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, timezone.utc)


def generated_slugs(asset: str, now: float) -> list[str]:
    """Current and next window of each short family (Polymarket lists them ~1 day ahead; the tag
    listing does not return most of them). 4h windows are aligned to 00:00 ET = 04:00Z / 05:00Z, so
    both alignments are tried and the 404 is cached as empty."""
    out = []
    for name, w in WINDOWS.items():
        offsets = (0,) if name != "4h" else (0, 3600)
        for off in offsets:
            base = (int(now - off) // w) * w + off
            for k in (0, 1):
                out.append(f"{asset}-updown-{name}-{base + k * w}")
    return out


def _market_record(ev: dict, m: dict) -> dict | None:
    try:
        tokens = json.loads(m.get("clobTokenIds") or "[]")
        outcomes = json.loads(m.get("outcomes") or "[]")
    except ValueError:
        return None
    if not tokens or not m.get("enableOrderBook", True) or m.get("closed"):
        return None
    start = m.get("eventStartTime") or m.get("startDate")
    return {"event_slug": ev.get("slug"), "family": family(ev.get("slug", "")),
            "market_slug": m.get("slug"), "item": m.get("groupItemTitle"),
            "condition_id": m.get("conditionId"), "token": tokens[0], "outcome": outcomes[0] if outcomes else None,
            "start": start, "end": m.get("endDate"), "fee_schedule": m.get("feeSchedule"),
            "crypto_config": m.get("cryptoMarketConfig"), "resolution_source": m.get("resolutionSource"),
            "description": m.get("description"), "tick": m.get("orderPriceMinTickSize"),
            "min_size": m.get("orderMinSize")}


def refresh_catalog(assets: list[str], tags: list[str], seen: dict, cat_file: Path) -> dict:
    now = _now()
    events = []
    for tag in tags:
        events += active_events(tag)
    for a in assets:
        for slug in generated_slugs(a, now):
            ev = event_by_slug(slug)
            if ev:
                events.append(ev)
    live = {}
    for ev in events:
        if family(ev.get("slug", "")) is None:
            continue
        for m in ev.get("markets", []):
            rec = _market_record(ev, m)
            if rec is None or rec["end"] is None:
                continue
            end = datetime.fromisoformat(rec["end"].replace("Z", "+00:00")).timestamp()
            if end < now:
                continue
            rec["end_ts"] = end
            st = rec["start"]
            rec["start_ts"] = datetime.fromisoformat(st.replace("Z", "+00:00")).timestamp() if st else None
            live[rec["token"]] = rec
            if rec["token"] not in seen:
                seen[rec["token"]] = True
                with open(cat_file, "a") as f:
                    f.write(json.dumps({**rec, "first_seen": _iso(now).isoformat()}) + "\n")
    return live


def due(rec: dict, now: float, last: dict) -> bool:
    started = rec["start_ts"] is None or rec["start_ts"] <= now
    fast = started and rec["end_ts"] - now <= 3600
    return now - last.get(rec["token"], 0) >= (FAST_S if fast else SLOW_S)


def fetch_books(tokens: list[str]) -> list[dict]:
    out = []
    for i in range(0, len(tokens), 200):
        chunk = tokens[i:i + 200]
        for attempt in range(3):
            try:
                r = requests.post(f"{CLOB}/books", json=[{"token_id": t} for t in chunk], timeout=20)
                if r.status_code == 200:
                    out += r.json()
                    break
            except (requests.RequestException, ValueError):
                pass
            time.sleep(2 ** attempt)
    return out


def slim(b: dict, recv: float) -> dict:
    bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])), reverse=True)[:LEVELS]
    asks = sorted((float(x["price"]), float(x["size"])) for x in b.get("asks", []))[:LEVELS]
    return {"recv": round(recv, 3), "ts": int(b.get("timestamp", 0)), "token": b.get("asset_id"),
            "hash": b.get("hash"), "bids": bids, "asks": asks, "last": b.get("last_trade_price")}


def dir_gb(p: Path) -> float:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 2**30


def run(out: Path, assets: list[str], tags: list[str], max_gb: float, min_free_gb: float,
        max_cycles: int | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    cat_file = out / "catalog.jsonl"
    seen = {}
    if cat_file.exists():
        for line in cat_file.read_text().splitlines():
            seen[json.loads(line)["token"]] = True
    live, last, last_cat, cycles, size_checked, size = {}, {}, 0.0, 0, 0.0, dir_gb(out)
    while not _stop:
        now = _now()
        if now - last_cat >= CATALOG_S:
            try:
                live = refresh_catalog(assets, tags, seen, cat_file)
            except RuntimeError as e:
                print(f"{_iso(now):%H:%M:%S} catalog refresh failed: {e}", flush=True)
            last_cat = now
        if now - size_checked >= 60:
            size, size_checked = dir_gb(out), now
            free = shutil.disk_usage(out).free / 2**30
            if size > max_gb or free < min_free_gb:
                (out / "STOPPED.json").write_text(json.dumps(
                    {"at": _iso(now).isoformat(), "dir_gb": size, "free_gb": free,
                     "max_gb": max_gb, "min_free_gb": min_free_gb}))
                print(f"guard stop: dir {size:.2f} GiB, free {free:.1f} GiB", flush=True)
                return
        todo = [t for t, r in live.items() if r["end_ts"] > now and due(r, now, last)]
        if todo:
            books = fetch_books(todo)
            recv = _now()
            path = out / _iso(recv).strftime("%Y-%m-%d") / f"{_iso(recv):%H}.jsonl.gz"
            path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(path, "at") as f:
                for b in books:
                    f.write(json.dumps(slim(b, recv), separators=(",", ":")) + "\n")
            for t in todo:
                last[t] = now
        cycles += 1
        if max_cycles and cycles >= max_cycles:
            return
        time.sleep(max(0.0, 1.0 - (_now() - now)))


def _handle(signum, frame):
    global _stop
    _stop = True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--assets", default="btc")
    ap.add_argument("--tags", default="bitcoin")
    ap.add_argument("--max-gb", type=float, default=3.0)
    ap.add_argument("--min-free-gb", type=float, default=55.0)
    ap.add_argument("--max-cycles", type=int, default=None)
    a = ap.parse_args()
    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)
    run(a.out, a.assets.split(","), a.tags.split(","), a.max_gb, a.min_free_gb, a.max_cycles)
