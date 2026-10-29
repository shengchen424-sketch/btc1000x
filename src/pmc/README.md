# pmc — Polymarket crypto window research

Plan: `docs/POLYMARKET_CRYPTO_PLAN.md`. Read-only public endpoints; no key, no signing, no orders.
Kept self-contained so it can move to `/root/polymarket-btc-hunter` later.

| module | what |
|---|---|
| `families.py` | slug → family, verified resolution rules, taker fee (`rate * (p(1-p))**exponent`) |
| `census.py` | live market census: rules, fee schedules, ticks, liquidity (`research/results/PM-CENSUS/`) |
| `collector.py` | forward CLOB book collector (the only source of Polymarket book history) |
| `spot.py` | Binance spot klines from the public archive (hourly / daily markets resolve on spot) |

## Install the collector on the VPS (owner-approved 2026-10-29)

```
cd /root/btc1000x && git fetch origin claude/friendly-archimedes-2em0q4 && git checkout claude/friendly-archimedes-2em0q4
. .venv/bin/activate && pip install -e . && python -m pytest tests/pmc
mkdir -p /root/polymarket-btc-hunter/data/pm_books
python -m pmc.collector --out /tmp/pm_test --max-cycles 30      # smoke test, then rm -r /tmp/pm_test
cp ops/pm-book-collector.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now pm-book-collector
journalctl -u pm-book-collector -n 20 ; du -sh /root/polymarket-btc-hunter/data/pm_books
```

Limits: 3 GiB output cap (measured ~55 MB/day → about 7 weeks), stops below 55 GiB free disk
(host GUARD_POLICY), `MemoryMax=300M`, `CPUQuota=20%`, `Nice=19`, idle IO. A guard stop writes
`STOPPED.json` and exits; systemd does not restart a clean exit. Stop: `systemctl disable --now pm-book-collector`.

Output: `catalog.jsonl` (each market's rule text, fee schedule, token id when first seen) and
`YYYY-MM-DD/HH.jsonl.gz` (one line per book: receive time, book timestamp, top 8 bids/asks).
Nothing reads these outcomes until a registered experiment says so.

Known gap: the Chainlink TWAP-60s stream itself is not archived (Data Streams need credentials);
5m/15m/4h research uses Binance spot as the proxy (EXP-016a: 99 % outcome agreement on 5m/15m).
