# EXP-008 — Daily volatility-compression breakout: 0/4, closed

Run 2026-10-14 on commit `f1dad82`.

| Rule | TRAIN CAGR / Sharpe / max DD | VAL CAGR / Sharpe / max DD | VAL p | VAL by year | gate |
|---|---|---|---|---|---|
| q 0.10 LONG | -17.5 % / -0.99 / 50 % | +20.7 % / 0.94 / 19 % | 0.092 | 2023 +26 %, 2024 +16 % | FAIL (p, Sharpe < 1) |
| q 0.20 LONG | -2.9 % / 0.03 / 50 % | +20.3 % / 0.91 / 19 % | 0.099 | 2023 +26 %, 2024 +15 % | FAIL |
| q 0.10 SHORT | +0.8 % / 0.13 / 31 % | -4.3 % / -0.19 / 17 % | 0.61 | | FAIL |
| q 0.20 SHORT | +21.1 % / 0.86 / 30 % | -6.3 % / -0.30 / 21 % | 0.67 | | FAIL |
| buy and hold | +10.9 % / 0.52 / 79 % | +115 % / 1.81 / 29 % | | | |

The long breakouts earned +20 % a year in the 2023–24 bull with 20 % time in market, which is a
fraction of buy-and-hold with the same drawdown ratio, and lost 18 %/yr on TRAIN. The short side is
the mirror image across periods. Whichever side you pick, it is the period's direction, not the
compression. Closed.
