from pmc.collector import generated_slugs, slim
from pmc.families import family, taker_cost_share, taker_fee_per_share


def test_family_patterns():
    assert family("btc-updown-15m-1793286000") == "updown_15m"
    assert family("btc-updown-4h-1793275200") == "updown_4h"
    assert family("bitcoin-up-or-down-october-29-2026-10am-et") == "updown_1h"
    assert family("bitcoin-up-or-down-on-october-29-2026") == "updown_1d"
    assert family("bitcoin-above-on-october-30-2026") == "above_1d"
    assert family("bitcoin-price-on-october-30-2026") == "range_1d"
    assert family("what-price-will-bitcoin-hit-october-26-november-1-2026") == "hit_week"
    assert family("what-price-will-bitcoin-hit-in-october-2026") == "hit_month"
    assert family("when-will-bitcoin-hit-150k") is None


def test_fee_matches_help_centre_example():
    # 100 shares at 0.50 -> $1.75 (Polymarket help centre, crypto rate 0.07)
    assert abs(100 * taker_fee_per_share(0.5) - 1.75) < 1e-9
    assert abs(taker_cost_share(0.9) - (0.9 + 0.07 * 0.09)) < 1e-12


def test_generated_slugs_aligned():
    s = generated_slugs("btc", 1793286100.0)
    assert "btc-updown-15m-1793286000" in s and "btc-updown-15m-1793286900" in s
    assert "btc-updown-5m-1793286000" in s
    assert "btc-updown-4h-1793275200" in s


def test_slim_sorts_best_first():
    b = {"asset_id": "x", "timestamp": "1", "hash": "h", "last_trade_price": "0.5",
         "bids": [{"price": "0.01", "size": "9"}, {"price": "0.49", "size": "5"}],
         "asks": [{"price": "0.99", "size": "9"}, {"price": "0.51", "size": "5"}]}
    r = slim(b, 0.0)
    assert r["bids"][0] == (0.49, 5.0) and r["asks"][0] == (0.51, 5.0)
