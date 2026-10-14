# EXP-011 — Polymarket daily temperature: market is calibrated; ensemble test infeasible on free data

Run 2026-10-14. Owner decision (after reading Weather Quant): no further weather research; this closes the line.

## Part A — market calibration (descriptive), 377 events, 13 cities, 2026-09-15 .. 2026-10-13
Prices at 06:00 UTC on the observation day, 4,147 priced buckets (buckets with no trade before 06Z excluded):

| Statistic | 06:00 UTC D | 12:00 UTC D-1 |
|---|---|---|
| Brier score of bucket prices | **0.058** | 0.062 |
| Brier of a uniform 1-of-11 guess | 0.083 | 0.083 |
| Mean sum of bucket prices (overround) | 1.026 | 1.030 |

Reliability at 06Z: priced 0.05–0.10 -> hit 7.6 %; 0.10–0.20 -> 11.5 %; 0.20–0.30 -> 25.9 %; 0.30–0.50 -> 39.8 %;
0.50–0.70 -> 53.3 %. The market is well calibrated at every price level, with a 2.6 % overround; the
5 % x p(1-p) taker fee sits on top of that. To profit, a forecast must beat a Brier of 0.058.

## Part B — GFS ensemble vs market: INFEASIBLE with public data
Open-Meteo's ensemble endpoint returns member values only for the current and ~3 previous days;
`past_days=92` returns the dates but null members. The previous-runs / historical-forecast endpoints
are rate-limited from this session's shared address. Overlap with priced events: 3 days per city.
No forecast-vs-market statistic was computed; the registered gate is NO_EVIDENCE by construction.

Polymarket price history itself is retained only from ~2026-09-15 for resolved markets (public-search
returned a spring-2026 subset with empty histories; slug lookups confirm the retention edge).

## What it would take (recorded, not planned)
A daily archive of GEFS/ECMWF-ENS members at the resolution stations (NOMADS/AWS GRIB, or Open-Meteo
previous-runs from an unshared address) and the CLOB book at 06Z, accumulated forward for 2–3 months.
Weather Quant's #16/#28/#30 already report the market beating station-EMOS models by 19–57 % in
log-loss; nothing here contradicts that.
