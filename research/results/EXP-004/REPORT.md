# EXP-004 — Daily-close trend on the perpetual: 3 LEADs (long rules), 0 CANDIDATE; shorts fail

Run 2026-10-14 on commit `ead9bfc`. Daily-clock position simulator with realised funding; fees 6 bps +
3 bps slippage per position change. VALIDATION 2023-01-01 .. 2024-12-31 (731 days).

| Rule | VAL CAGR | Sharpe | max DD | MAR | p (daily) | years + | funding paid | in market | gate |
|---|---|---|---|---|---|---|---|---|---|
| T7_L (SMA200 + 55/20 breakout) | +61 % | 1.52 | 17 % | 3.56 | 0.016 | 2/2 | 13.6 % | 46 % | **LEAD** |
| DON_L (55/20 Donchian) | +66 % | 1.58 | 21 % | 3.21 | 0.013 | 2/2 | 13.8 % | 48 % | **LEAD** |
| SMA200_L | +71 % | 1.43 | 29 % | 2.48 | 0.022 | 2/2 | 18.8 % | 80 % | **LEAD** |
| T7_S / DON_S / SMA200_S | -23 % .. -36 % | < 0 | 41–59 % | < 0 | > 0.95 | 0/2 | | | FAIL |
| Buy and hold perp (funding paid) | +115 % | 1.81 | 29 % | 3.92 | | 2/2 | 19.8 % | 100 % | baseline |

TRAIN (2020–22) for context: T7_L CAGR +22 %, Sharpe 0.76, max DD 39 %, MAR 0.57 vs buy-and-hold
CAGR +11 %, max DD 79 %, MAR 0.14. Funding paid while long cost 30 % of notional over the three years.

## Reading

1. The three long rules pass the LEAD bar (Sharpe > 0.7, p < 0.05, both years positive) but not
   CANDIDATE: in 2023–24 buy-and-hold had a higher MAR (3.9 vs 3.6) because the period was a bull
   market with one 29 % drawdown. The rules' value shows in bear years (2022: they are flat, buy-and-hold
   loses 65 %), which VALIDATION does not contain.
2. All short rules lose in both periods: BTC perpetual shorts on daily trend rules did not pay even in
   2022 on TRAIN (T7_S CAGR -18 %). The short side is closed.
3. Funding is the perpetual's tax on this family: 13–19 % of notional over two years. On spot it would
   not exist, which is why the owner's earlier project found the spot version stronger.
4. Feasibility at 10 USDT: one lot is a 0.84x position. The rules have no fixed stop; the planned risk
   is the exit rule's adverse excursion (17–39 % drawdowns). That is outside RISK defaults (1 % per
   trade) and the risk engine would reject it. At 2x isolated leverage one lot needs ~4.2 USDT margin and
   liquidates ~49 % down, beyond any observed drawdown of T7_L; at 5x it liquidates at ~19 %, inside
   TRAIN's 39 % drawdown. Any live use of this family is a separate owner decision on risk per trade.

## Consequence (per registration)

T7_L, DON_L and SMA200_L enter the shadow registry as LEAD for forward observation only: the shadow
runner logs their target position after each 00:00 UTC close from Bitget's own daily candles, with
the timestamp, before the next day's outcome exists. No order. No champion status. They may be
promoted only by a registered confirmation on data not used here (the sealed 2025-01 .. 2026-09
holdout, which contains a drawdown period, plus the forward record).
