# EXP-013 — Incremental alpha on the flow book: 0 of 5 features adopted

Run 2026-10-14 on commit `71d7563`. Paired B − A on the same days, 7 offsets pooled, independent window
2025-01-01 .. 2026-09-30 (638 days), sign check on 2023–24. Baseline A on 2025–26: Sharpe 2.12, max DD 15.3 %.

| Feature | 2025–26 Δ ann. return | CI95 | p | 2023–24 Δ | B Sharpe / DD | gate |
|---|---|---|---|---|---|---|
| F1a BTC near-high gate, long leg halved | +1.4 % | [-12.0, +14.5] | 0.41 | -12.7 % | 2.09 / 15.3 % | DISCARD |
| F1b BTC near-high gate, both legs halved | -0.5 % | [-9.5, +7.8] | 0.55 | -11.5 % | 2.20 / 15.3 % | DISCARD |
| F2a skip shorts paying > 0.05 %/8h funding | -4.4 % | [-9.9, +0.4] | 0.95 | +0.6 % | 2.00 / 15.3 % | DISCARD |
| F2b skip longs paying > 0.05 %/8h funding | +6.4 % | [-6.0, +19.2] | 0.16 | -2.1 % | **2.44 / 13.8 %** | DISCARD (sign flips) |
| F3 ETH/BTC 30-day negative -> long leg halved | -3.9 % | [-25.3, +17.9] | 0.63 | -30.0 % | 2.04 / 14.3 % | DISCARD |

## Reading
- No overlay changes the 2025–26 return by an amount distinguishable from zero; the confidence
  intervals are ±10–20 %/yr wide because the book's returns are tail-driven (ST-AUDIT-001), so 638
  days cannot resolve a 5 %/yr improvement. This is a property of the strategy, not of the test.
- The regime gates (F1, F3) cost 12–30 %/yr in 2023–24: cutting the long leg when BTC is near highs
  or alts are weak removes exactly the lottery positions that carry the book.
- F2b (avoid crowded longs) is the only feature that raises Sharpe and lowers drawdown in the
  independent window, but its 2023–24 sign is negative and its CI spans zero. Recorded as the one
  idea worth a forward-shadow comparison (two books side by side), not as an improvement.
- Skipping crowded shorts (F2a) hurts: the shorts that pay heavy funding are the ones that fall.

## Consequence
The simple-overlay family is closed on this history. Further incremental tests need either a longer
independent window (forward) or a feature with a sharper mechanism than a regime gate. The baseline
book stays as is.
