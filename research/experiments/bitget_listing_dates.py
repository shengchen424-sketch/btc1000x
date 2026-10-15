"""Historical Bitget listing date per symbol = first daily candle available from history-candles
(paged backwards, 200 bars per call). Needed to judge executability at the time of each position,
not with today's contract list. Writes evidence/exchange/bitget_listing_dates.json."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone

import requests

from b1k.config import PATHS

S = requests.Session()
S.headers["User-Agent"] = "btc1000x-research/0.1"
OUT = PATHS.evidence / "exchange" / "bitget_listing_dates.json"


def first_bar_ms(symbol: str) -> int | None:
    end = int(time.time() * 1000)
    first = None
    for _ in range(60):
        for a in range(3):
            try:
                r = S.get("https://api.bitget.com/api/v2/mix/market/history-candles",
                          params={"productType": "USDT-FUTURES", "symbol": symbol, "granularity": "1D", "limit": 200, "endTime": end}, timeout=30)
                j = r.json()
                break
            except Exception:
                time.sleep(1 + a); j = {}
        d = j.get("data") or []
        if not d:
            break
        lo = min(int(x[0]) for x in d)
        if first is not None and lo >= first:
            break  # no progress: endpoint returned the same page
        first = lo
        end = lo - 1  # the endpoint serves at most 90 daily bars per call: page until empty
        time.sleep(0.12)
    return first


def main(symfile: str) -> None:
    syms = [l.strip() for l in open(symfile) if l.strip()]
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for i, s in enumerate(syms):
        if s in out and out[s].get("complete"):
            continue
        fb, used = None, None
        for cand in [s, s.replace("1000", "", 1) if s.startswith("1000") else None]:
            if not cand:
                continue
            fb = first_bar_ms(cand)
            if fb:
                used = cand
                break
        out[s] = {"first_daily_bar_ms": fb, "first_daily_bar": datetime.fromtimestamp(fb / 1000, tz=timezone.utc).date().isoformat() if fb else None,
                  "bitget_symbol": used, "complete": True}
        if i % 20 == 0:
            OUT.write_text(json.dumps(out, indent=1)); print(i, s, out[s]["first_daily_bar"], flush=True)
    out["_fetched"] = datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(out, indent=1))
    print("done", len(out))


if __name__ == "__main__":
    main(sys.argv[1])
