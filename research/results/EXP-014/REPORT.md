# EXP-014 — Residual momentum is a real signal on this universe, but half-correlated with the flow book

Run 2026-10-14 on commit `a6213c5`. Same engine as the flow book (top-30 universe, weekly 5+5, 10 bps,
funding, trim, 7 offsets pooled). Baseline A = the reproduced flow book.

| Book | 2025–26 ann. | Sharpe | max DD | p | CI95 ann. | 2023–24 ann. / Sharpe | corr with A | 50/50 mix Sharpe / DD (A: 2.12 / 15.3 %) | gate |
|---|---|---|---|---|---|---|---|---|---|
| RM7 residual momentum, 7d | +25 % | 0.79 | 36 % | 0.15 | [-22, +85] | +22 % / 0.94 | 0.32 | 1.77 / 21.8 % | DISCARD |
| **RM14 residual momentum, 14d** | **+93 %** | **1.77** | 33 % | **0.0099** | [+13, +141] | +58 % / 1.73 | **0.47** | 2.25 / 21.2 % | DISCARD (correlation) |
| **CAM14 carry-adjusted, 14d** | +90 % | 1.76 | 33 % | 0.0102 | [+13, +138] | +55 % / 1.66 | 0.49 | 2.23 / 19.0 % | DISCARD (correlation) |
| CARRY control (funding rank) | -9 % | -0.05 | 45 % | 0.53 | [-56, +52] | +41 % / 1.42 | 0.10 | 1.35 / 19.0 % | control |

## Reading
- **14-day BTC-hedged residual momentum passes every standalone gate** (p < 0.0167 in the independent
  window, positive and significant in 2023–24 as well) on identical execution and costs. The 7-day
  version does not: idiosyncratic continuation lives at the two-week horizon here.
- It is **not independent of the flow factor**: daily correlation 0.47–0.49 against the registered
  0.30 ceiling, so by the registration it is DISCARDED as independent alpha. The reason is
  mechanical: coins with a week of one-sided taker buying have, by construction, positive 14-day
  residual returns. The two rankings overlap heavily.
- Portfolio value is therefore modest: a 50/50 mix lifts Sharpe from 2.12 to 2.25 while the maximum
  drawdown goes from 15 % to 21 %, because RM14 has its own 33 % drawdown.
- Subtracting the expected funding cost (CAM14) changes nothing measurable: the funding term is small
  next to a 14-day residual return.
- **Carry alone has decayed**: +41 %/yr and Sharpe 1.4 in 2023–24, -9 % and Sharpe -0.05 in 2025–26
  (consistent with LIT-001: carry Sharpe fell to negative in 2025). Its correlation with the flow book
  is only 0.10, so the flow book is not a carry strategy.

## Consequence
RM14 is the strongest non-flow signal found in this program. Under the owner's framework the right
follow-up is not a second book but an incremental test: does adding residual momentum to the flow
RANKING improve the single book (B − A)? Registered as EXP-015. RM14 standalone is recorded as a
candidate for a parallel forward shadow if the owner wants a second validated book despite the
correlation; it is not adopted here.
