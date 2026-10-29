"""Market families, their resolution rules (verified from market descriptions 2026-10-29) and fees."""
from __future__ import annotations

import re

# family -> (resolution source, rule). Re-checked by pmc.census against every live description.
RULES = {
    "updown_5m":  ("chainlink_twap60", "Chainlink BTC/USD TWAP-60s at window end >= at window start (end-point reading, EXP-016a)"),
    "updown_15m": ("chainlink_twap60", "Chainlink BTC/USD TWAP-60s at window end >= at window start (end-point reading, EXP-016a)"),
    "updown_4h":  ("chainlink_twap60", "Chainlink BTC/USD TWAP-60s at window end >= at window start (end-point reading, EXP-016a)"),
    "updown_1h":  ("binance_spot_1h", "1h candle close >= open"),
    "updown_1d":  ("binance_spot_1m", "1m close at 12:00 ET today > same yesterday (equal -> 50/50)"),
    "above_1d":   ("binance_spot_1m", "1m close at 12:00 ET on the date > strike"),
    "range_1d":   ("binance_spot_1m", "1m close at 12:00 ET on the date in bracket (tie -> higher)"),
    "hit_week":   ("binance_spot_1m", "any 1m high >= strike (low <= strike for down) within the week"),
    "hit_month":  ("binance_spot_1m", "any 1m high >= strike (low <= strike for down) within the month"),
}

_PATTERNS = [
    (r"^(btc|eth|sol|xrp)-updown-5m-\d+$", "updown_5m"),
    (r"^(btc|eth|sol|xrp)-updown-15m-\d+$", "updown_15m"),
    (r"^(btc|eth|sol|xrp)-updown-4h-\d+$", "updown_4h"),
    (r"^(bitcoin|ethereum|solana|xrp)-up-or-down-[a-z]+-\d+-\d{4}-\d+(am|pm)-et$", "updown_1h"),
    (r"^(bitcoin|ethereum|solana|xrp)-up-or-down-on-[a-z]+-\d+-\d{4}$", "updown_1d"),
    (r"^(bitcoin|ethereum|solana|xrp)-above-on-[a-z]+-\d+-\d{4}$", "above_1d"),
    (r"^(bitcoin|ethereum|solana|xrp)-price-on-[a-z]+-\d+-\d{4}$", "range_1d"),
    (r"^what-price-will-(bitcoin|ethereum|solana|xrp)-hit-[a-z]+-\d+-[a-z]+-\d+-\d{4}$", "hit_week"),
    (r"^what-price-will-(bitcoin|ethereum|solana|xrp)-hit-in-[a-z]+-\d{4}$", "hit_month"),
]


def family(slug: str) -> str | None:
    for pat, fam in _PATTERNS:
        if re.match(pat, slug):
            return fam
    return None


def taker_fee_per_share(price: float, rate: float = 0.07, exponent: float = 1.0) -> float:
    """Polymarket feeSchedule (crypto_fees_v2): fee = shares * rate * (p * (1 - p)) ** exponent.
    Makers pay none (takerOnly). Read rate/exponent from each market's feeSchedule, not this default."""
    return rate * (price * (1.0 - price)) ** exponent


def taker_cost_share(price: float, rate: float = 0.07, exponent: float = 1.0) -> float:
    """All-in cost of buying one share at `price` as a taker (price + fee)."""
    return price + taker_fee_per_share(price, rate, exponent)
